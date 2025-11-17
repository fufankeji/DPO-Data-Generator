#!/usr/bin/env python3
"""
AutoToolDPO 主控制器
企业级 Agent 工具调用 DPO 数据集自动构建系统

作者：muyan - 赋范空间
版本：1.0.0
"""

import asyncio
import argparse
from pathlib import Path
from typing import Optional
import sys

# 添加当前目录到系统路径
sys.path.insert(0, str(Path(__file__).parent))

from core.tool_registry import ToolRegistry
from core.task_generator import TaskGenerator
from core.data_synthesizer import DataSynthesizer
from core.validator import Validator
from core.exporter import Exporter
from core.concurrent_engine import ConcurrentEngine, ProgressStats
from services.llm_client import LLMClient
from core.utils import setup_logger, ensure_dir


class AutoToolDPO:
    """AutoToolDPO 主控制器"""

    def __init__(self, config: dict):
        """
        初始化控制器

        Args:
            config: 配置字典
        """
        self.config = config
        self.logger = setup_logger("AutoToolDPO", log_file="logs/generation.log")

        # 初始化组件
        self.tool_registry = None
        self.task_generator = None
        self.llm_client = None
        self.synthesizer = None
        self.validator = None
        self.exporter = None
        self.engine = None

    def initialize(self):
        """初始化所有组件"""
        self.logger.info("=" * 80)
        self.logger.info("AutoToolDPO 系统初始化")
        self.logger.info("=" * 80)

        # 1. 加载工具注册中心
        self.logger.info(f"加载工具配置: {self.config['tool_list_path']}")
        self.tool_registry = ToolRegistry(self.config["tool_list_path"])

        # 2. 初始化任务生成器
        self.task_generator = TaskGenerator(self.tool_registry)

        # 3. 初始化LLM客户端
        self.logger.info(f"初始化LLM客户端: {self.config['base_model']}")
        self.llm_client = LLMClient(
            api_url=self.config["model_api_url"],
            api_key=self.config.get("api_key"),
            model=self.config["base_model"],
            timeout=self.config.get("timeout", 60)
        )

        # 4. 初始化数据合成器
        self.synthesizer = DataSynthesizer(self.llm_client)

        # 5. 初始化验证器
        self.validator = Validator(strict_mode=self.config.get("strict_validation", False))

        # 6. 初始化导出器
        ensure_dir(self.config["output_dir"])
        self.exporter = Exporter(self.config["output_dir"])

        # 7. 初始化并发引擎
        self.engine = ConcurrentEngine(
            synthesizer=self.synthesizer,
            validator=self.validator,
            concurrency=self.config["concurrency"]
        )

        # 添加进度回调
        self.engine.add_progress_callback(self._on_progress_update)

        self.logger.info("系统初始化完成")

    async def run(self):
        """执行数据生成流程"""
        self.logger.info("=" * 80)
        self.logger.info("开始数据生成流程")
        self.logger.info("=" * 80)

        # 1. 生成任务
        self.logger.info(f"生成 {self.config['num_samples']} 个任务...")

        tool_count_range = None
        if self.config.get("tool_count_mode") == "range":
            tool_count_range = (
                self.config.get("tool_count_min", 2),
                self.config.get("tool_count_max", 5)
            )

        tasks = self.task_generator.generate_tasks(
            num_samples=self.config["num_samples"],
            multi_ratio=self.config["multi_ratio"],
            tool_count=self.config.get("tool_count", 3),
            tool_count_range=tool_count_range,
            seed=self.config.get("seed")
        )

        self.logger.info(f"任务生成完成: {len(tasks)} 个")

        # 2. 并发处理任务
        self.logger.info(f"开始并发处理任务（并发度={self.config['concurrency']}）...")

        valid_samples, invalid_samples = await self.engine.process_tasks(
            tasks=tasks,
            enable_validation=True,
            enable_correction=self.config.get("auto_correction", False)
        )

        self.logger.info(f"处理完成: 有效样本={len(valid_samples)}, 无效样本={len(invalid_samples)}")

        # 3. 导出数据
        self.logger.info("导出数据...")

        file_paths = self.exporter.export_to_jsonl(
            samples=valid_samples,
            filename="data_dpo.jsonl",
            batch_size=self.config.get("batch_size", 1000)
        )

        # 生成dataset_info.json
        dataset_info_path = self.exporter.generate_dataset_info(
            dataset_name="tool_dpo_dataset",
            file_name="data_dpo.jsonl" if len(file_paths) == 1 else "data_dpo_*.jsonl",
            config=self.config
        )

        # 导出统计信息
        stats = self.engine.get_stats()
        stats_path = self.exporter.export_statistics(stats)

        # 导出无效样本（调试用）
        if invalid_samples:
            invalid_path = self.exporter.export_invalid_samples(invalid_samples)
            self.logger.info(f"无效样本已导出: {invalid_path}")

        # 4. 生成摘要
        summary = self.exporter.get_export_summary(file_paths)

        self.logger.info("=" * 80)
        self.logger.info("数据生成完成")
        self.logger.info("=" * 80)
        self.logger.info(f"输出目录: {self.config['output_dir']}")
        self.logger.info(f"数据文件数量: {summary['file_count']}")
        self.logger.info(f"总大小: {summary['total_size_mb']} MB")
        self.logger.info(f"有效样本: {len(valid_samples)}")
        self.logger.info(f"无效样本: {len(invalid_samples)}")
        self.logger.info(f"生成速率: {stats['rate']:.2f} 样本/秒")
        self.logger.info(f"验证成功率: {stats['validation_success_rate']:.2f}%")

    def _on_progress_update(self, stats: ProgressStats):
        """进度更新回调"""
        if stats.completed_tasks % 10 == 0:  # 每10个样本打印一次
            self.logger.info(
                f"进度: {stats.completed_tasks}/{stats.total_tasks} "
                f"({stats.progress_percent:.1f}%) | "
                f"速率: {stats.generation_rate:.2f} 样本/秒"
            )


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="AutoToolDPO - 企业级 Agent 工具调用 DPO 数据集自动构建系统"
    )

    parser.add_argument(
        "--num_samples",
        type=int,
        default=1000,
        help="生成样本数量 (默认: 1000)"
    )

    parser.add_argument(
        "--multi_ratio",
        type=float,
        default=0.3,
        help="多轮对话比例 0-1 (默认: 0.3)"
    )

    parser.add_argument(
        "--tool_count",
        type=int,
        default=3,
        help="每个任务使用的工具数量 (默认: 3)"
    )

    parser.add_argument(
        "--tool_count_mode",
        type=str,
        choices=["single", "range"],
        default="single",
        help="工具数量模式: single(固定值) 或 range(范围) (默认: single)"
    )

    parser.add_argument(
        "--tool_count_min",
        type=int,
        default=2,
        help="工具数量范围最小值 (默认: 2)"
    )

    parser.add_argument(
        "--tool_count_max",
        type=int,
        default=5,
        help="工具数量范围最大值 (默认: 5)"
    )

    parser.add_argument(
        "--concurrency",
        type=int,
        default=10,
        help="并发请求数 (默认: 10)"
    )

    parser.add_argument(
        "--tool_list_path",
        type=str,
        default="backend/configs/tools_registry.json",
        help="工具列表配置文件路径"
    )

    parser.add_argument(
        "--base_model",
        type=str,
        default="gpt-3.5-turbo",
        help="基础模型名称 (默认: gpt-3.5-turbo)"
    )

    parser.add_argument(
        "--model_api_url",
        type=str,
        default="https://api.openai.com/v1",
        help="模型API地址 (默认: OpenAI API)"
    )

    parser.add_argument(
        "--api_key",
        type=str,
        default=None,
        help="API密钥"
    )

    parser.add_argument(
        "--output_dir",
        type=str,
        default="data/processed",
        help="输出目录 (默认: data/processed)"
    )

    parser.add_argument(
        "--batch_size",
        type=int,
        default=1000,
        help="每个文件的样本数量 (默认: 1000)"
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="随机种子"
    )

    return parser.parse_args()


def main():
    """主函数"""
    # 解析参数
    args = parse_arguments()

    # 构建配置
    config = vars(args)

    # 创建控制器
    controller = AutoToolDPO(config)

    # 初始化
    controller.initialize()

    # 运行
    try:
        asyncio.run(controller.run())
    except KeyboardInterrupt:
        controller.logger.info("用户中断，程序退出")
    except Exception as e:
        controller.logger.error(f"程序异常: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
