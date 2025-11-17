"""
FastAPI应用主文件
"""

import asyncio
import sys
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import Dict
import logging

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.models import (
    GenerationConfig,
    TaskCreateResponse,
    TaskStatusResponse,
    LogMessage,
    StatsUpdate
)
from core.tool_registry import ToolRegistry
from core.task_generator import TaskGenerator
from core.data_synthesizer import DataSynthesizer
from core.validator import Validator
from core.exporter import Exporter
from core.concurrent_engine import ConcurrentEngine, ProgressStats
from services.llm_client import LLMClient
from services.task_manager import TaskManager, TaskStatus
from core.utils import setup_logger, ensure_dir

# 创建FastAPI应用
app = FastAPI(
    title="AutoToolDPO API",
    description="企业级 Agent 工具调用 DPO 数据集自动构建系统 API",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局状态
task_manager = TaskManager()
websocket_clients: Dict[str, WebSocket] = {}
logger = setup_logger("API")


# WebSocket连接管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, task_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[task_id] = websocket
        logger.info(f"WebSocket连接建立: task_id={task_id}")

    def disconnect(self, task_id: str):
        if task_id in self.active_connections:
            del self.active_connections[task_id]
            logger.info(f"WebSocket连接断开: task_id={task_id}")

    async def send_log(self, task_id: str, level: str, message: str):
        """发送日志消息"""
        if task_id in self.active_connections:
            try:
                await self.active_connections[task_id].send_json({
                    "type": "log",
                    "level": level,
                    "data": message
                })
            except Exception as e:
                logger.error(f"发送日志失败: {str(e)}")

    async def send_stats(self, task_id: str, stats: Dict):
        """发送统计更新"""
        if task_id in self.active_connections:
            try:
                await self.active_connections[task_id].send_json({
                    "type": "stats",
                    "data": stats
                })
            except Exception as e:
                logger.error(f"发送统计失败: {str(e)}")


manager = ConnectionManager()


async def run_generation_task(task_id: str, config: GenerationConfig):
    """后台运行生成任务"""
    try:
        # 更新任务状态
        await task_manager.start_task(task_id)
        await manager.send_log(task_id, "info", "任务开始执行")

        # 初始化组件
        await manager.send_log(task_id, "info", f"加载工具配置: {config.tool_list_path}")
        tool_registry = ToolRegistry(config.tool_list_path)
        await manager.send_log(task_id, "success", f"成功加载 {len(tool_registry.tools)} 个工具")

        task_generator = TaskGenerator(tool_registry)
        await manager.send_log(task_id, "info", "初始化任务生成器...")

        await manager.send_log(task_id, "info", f"初始化LLM客户端: {config.base_model}")
        llm_client = LLMClient(
            api_url=config.model_api_url,
            api_key=config.api_key,
            model=config.base_model
        )

        # 启用智能rejected策略（默认开启）
        synthesizer = DataSynthesizer(llm_client, enable_smart_rejected=True)

        # 启用LLM自评验证（将llm_client传给validator）
        validator = Validator(strict_mode=config.strict_validation, llm_client=llm_client)

        ensure_dir(config.output_dir)
        exporter = Exporter(config.output_dir)
        await manager.send_log(task_id, "info", "组件初始化完成（智能rejected策略：开启，LLM自评：可用）")

        engine = ConcurrentEngine(
            synthesizer=synthesizer,
            validator=validator,
            concurrency=config.concurrency
        )

        # 添加进度回调
        last_completed = [0]  # 记录上次已完成的任务数

        def progress_callback(stats: ProgressStats):
            asyncio.create_task(task_manager.update_progress(task_id, stats.progress_percent, stats.to_dict()))
            asyncio.create_task(manager.send_stats(task_id, stats.to_dict()))

            # 每完成一个任务发送日志
            if stats.completed_tasks > last_completed[0]:
                last_completed[0] = stats.completed_tasks
                asyncio.create_task(manager.send_log(
                    task_id,
                    "info",
                    f"进度: 已完成 {stats.completed_tasks}/{stats.total_tasks} 个任务 ({stats.progress_percent:.1f}%)"
                ))

        engine.add_progress_callback(progress_callback)

        # 添加日志回调
        async def log_callback(message: str):
            await manager.send_log(task_id, "info", message)

        engine.add_log_callback(log_callback)

        # 生成任务
        await manager.send_log(task_id, "info", f"生成 {config.num_samples} 个任务...")

        tool_count_range = None
        if config.tool_count_mode == "range":
            tool_count_range = (config.tool_count_min, config.tool_count_max)

        tasks = task_generator.generate_tasks(
            num_samples=config.num_samples,
            multi_ratio=config.multi_ratio,
            tool_count=config.tool_count,
            tool_count_range=tool_count_range,
            seed=config.seed
        )

        await manager.send_log(task_id, "success", f"任务生成完成: {len(tasks)} 个")

        # 并发处理
        await manager.send_log(task_id, "info", f"开始并发处理（并发度={config.concurrency}）...")

        valid_samples, invalid_samples = await engine.process_tasks(
            tasks=tasks,
            enable_validation=True,
            enable_correction=config.auto_correction
        )

        # 获取最终统计数据
        final_stats = engine.get_stats()

        # 发送最终统计数据（包含验证成功率）
        await manager.send_stats(task_id, final_stats)

        await manager.send_log(
            task_id,
            "success",
            f"处理完成: 有效={len(valid_samples)}, 无效={len(invalid_samples)}, 验证成功率={final_stats['validation_success_rate']}%"
        )

        # 导出数据
        await manager.send_log(task_id, "info", f"导出 {len(valid_samples)} 个有效样本到JSONL...")

        file_paths = exporter.export_to_jsonl(
            samples=valid_samples,
            filename="data_dpo.jsonl",
            batch_size=config.batch_size
        )
        await manager.send_log(task_id, "success", f"数据已导出: {len(file_paths)} 个文件")

        await manager.send_log(task_id, "info", "生成dataset_info.json...")
        dataset_info_path = exporter.generate_dataset_info(
            dataset_name="tool_dpo_dataset",
            file_name="data_dpo.jsonl" if len(file_paths) == 1 else "data_dpo_*.jsonl",
            config=config.dict()
        )

        stats = engine.get_stats()
        stats_path = exporter.export_statistics(stats)
        await manager.send_log(task_id, "info", "统计信息已保存")

        if invalid_samples:
            invalid_path = exporter.export_invalid_samples(invalid_samples)
            await manager.send_log(task_id, "info", f"无效样本已保存: {len(invalid_samples)} 个")

        # 完成任务
        output_files = file_paths + [dataset_info_path, stats_path]
        await task_manager.complete_task(task_id, output_files, stats)

        await manager.send_log(task_id, "success", "任务完成！")

    except Exception as e:
        logger.error(f"任务执行失败: {str(e)}", exc_info=True)
        await task_manager.fail_task(task_id, str(e))
        await manager.send_log(task_id, "error", f"任务失败: {str(e)}")


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "AutoToolDPO API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy"}


@app.post("/api/generate/start", response_model=TaskCreateResponse)
async def start_generation(config: GenerationConfig, background_tasks: BackgroundTasks):
    """启动生成任务"""
    try:
        # 创建任务
        task_id = task_manager.create_task(config.dict())

        # 后台运行
        background_tasks.add_task(run_generation_task, task_id, config)

        return TaskCreateResponse(
            task_id=task_id,
            status="pending",
            message="任务已创建，正在启动..."
        )

    except Exception as e:
        logger.error(f"启动任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/generate/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """获取任务状态"""
    task_status = task_manager.get_task_status(task_id)

    if not task_status:
        raise HTTPException(status_code=404, detail="任务不存在")

    return TaskStatusResponse(**task_status)


@app.post("/api/generate/{task_id}/stop")
async def stop_task(task_id: str):
    """停止任务"""
    success = await task_manager.cancel_task(task_id)

    if not success:
        raise HTTPException(status_code=400, detail="无法停止任务")

    return {"message": "任务已停止"}


@app.get("/api/download/{task_id}")
async def download_dataset(task_id: str):
    """下载数据集（如果有多个文件，打包成ZIP）"""
    task = task_manager.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="任务尚未完成")

    if not task.output_files:
        raise HTTPException(status_code=404, detail="没有输出文件")

    # 获取所有JSONL文件
    jsonl_files = [f for f in task.output_files if f.endswith(".jsonl")]

    if not jsonl_files:
        raise HTTPException(status_code=404, detail="未找到数据文件")

    # 如果只有一个文件，直接返回
    if len(jsonl_files) == 1:
        file_path = jsonl_files[0]
        if not Path(file_path).exists():
            raise HTTPException(status_code=404, detail="文件不存在")

        return FileResponse(
            file_path,
            media_type="application/x-ndjson",
            filename=Path(file_path).name
        )

    # 如果有多个文件，打包成ZIP
    import zipfile
    import tempfile

    # 创建临时ZIP文件
    temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    temp_zip_path = temp_zip.name
    temp_zip.close()

    try:
        with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in jsonl_files:
                if Path(file_path).exists():
                    zipf.write(file_path, Path(file_path).name)

        return FileResponse(
            temp_zip_path,
            media_type="application/zip",
            filename=f"dataset_{task_id[:8]}.zip"
        )
    except Exception as e:
        # 清理临时文件
        if Path(temp_zip_path).exists():
            Path(temp_zip_path).unlink()
        raise HTTPException(status_code=500, detail=f"打包失败: {str(e)}")


@app.websocket("/api/logs/{task_id}")
async def websocket_logs(websocket: WebSocket, task_id: str):
    """WebSocket实时日志"""
    await manager.connect(task_id, websocket)

    try:
        while True:
            # 保持连接
            await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect(task_id)
    except Exception as e:
        logger.error(f"WebSocket错误: {str(e)}")
        manager.disconnect(task_id)


@app.get("/api/tasks")
async def list_tasks(status: str = None, limit: int = 100):
    """列出任务"""
    task_status_enum = None
    if status:
        try:
            task_status_enum = TaskStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的状态值")

    tasks = task_manager.list_tasks(status=task_status_enum, limit=limit)
    return {"tasks": tasks}


@app.get("/api/stats")
async def get_statistics():
    """获取系统统计"""
    return task_manager.get_statistics()


@app.get("/api/tools/preview")
async def preview_tools(path: str = "configs/tools_registry.json"):
    """预览工具配置文件

    路径说明：
    - 相对路径（如 "configs/tools_registry.json"）：相对于 backend/ 目录
    - 绝对路径（如 "/Users/.../backend/configs/..."）：使用完整路径
    """
    try:
        import json
        from pathlib import Path

        # 获取backend目录的绝对路径
        backend_dir = Path(__file__).parent.parent.resolve()

        # 处理路径
        if Path(path).is_absolute():
            # 绝对路径：直接使用
            config_path = Path(path)
        else:
            # 相对路径：从backend目录开始解析
            # 移除可能的 "backend/" 前缀，因为我们已经在backend目录了
            clean_path = path.replace("backend/", "").lstrip("/")
            config_path = backend_dir / clean_path

        logger.info(f"预览工具配置: 输入路径={path}, 解析路径={config_path}")

        if not config_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"配置文件不存在: {config_path}\n相对路径应该相对于backend目录，例如: configs/tools_registry.json"
            )

        with open(config_path, 'r', encoding='utf-8') as f:
            file_content = f.read()

        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(content=file_content, media_type="application/json")

    except HTTPException:
        raise
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"配置文件不存在: {path}"
        )
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=400,
            detail=f"配置文件格式错误: {str(e)}"
        )
    except Exception as e:
        logger.error(f"预览工具配置失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
