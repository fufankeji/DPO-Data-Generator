"""
任务管理器模块
负责管理生成任务的生命周期和状态
"""

import asyncio
import uuid
from typing import Dict, Optional, List
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field, asdict


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"          # 待处理
    RUNNING = "running"          # 运行中
    VALIDATING = "validating"    # 验证中
    COMPLETED = "completed"      # 已完成
    FAILED = "failed"            # 失败
    CANCELLED = "cancelled"      # 已取消


@dataclass
class GenerationTask:
    """生成任务"""
    task_id: str
    status: TaskStatus = TaskStatus.PENDING
    config: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    stats: Dict = field(default_factory=dict)
    output_files: List[str] = field(default_factory=list)
    error_message: Optional[str] = None

    def to_dict(self) -> Dict:
        """转换为字典"""
        data = asdict(self)
        data["status"] = self.status.value
        data["created_at"] = self.created_at.isoformat() if self.created_at else None
        data["started_at"] = self.started_at.isoformat() if self.started_at else None
        data["completed_at"] = self.completed_at.isoformat() if self.completed_at else None
        return data


class TaskManager:
    """任务管理器"""

    def __init__(self):
        """初始化任务管理器"""
        self.tasks: Dict[str, GenerationTask] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()

    def create_task(self, config: Dict) -> str:
        """
        创建新任务

        Args:
            config: 任务配置

        Returns:
            任务ID
        """
        task_id = str(uuid.uuid4())

        task = GenerationTask(
            task_id=task_id,
            config=config,
            status=TaskStatus.PENDING
        )

        self.tasks[task_id] = task
        return task_id

    async def start_task(self, task_id: str) -> bool:
        """
        启动任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功启动
        """
        async with self._lock:
            if task_id not in self.tasks:
                return False

            task = self.tasks[task_id]
            if task.status != TaskStatus.PENDING:
                return False

            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()

            return True

    async def update_progress(
        self,
        task_id: str,
        progress: float,
        stats: Optional[Dict] = None
    ) -> None:
        """
        更新任务进度

        Args:
            task_id: 任务ID
            progress: 进度（0-100）
            stats: 统计信息
        """
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.progress = progress

            if stats:
                task.stats = stats

    async def complete_task(
        self,
        task_id: str,
        output_files: List[str],
        stats: Dict
    ) -> None:
        """
        完成任务

        Args:
            task_id: 任务ID
            output_files: 输出文件列表
            stats: 最终统计信息
        """
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.progress = 100.0
            task.output_files = output_files
            task.stats = stats

            # 清理运行中的任务引用
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]

    async def fail_task(self, task_id: str, error_message: str) -> None:
        """
        标记任务失败

        Args:
            task_id: 任务ID
            error_message: 错误信息
        """
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            task.error_message = error_message

            # 清理运行中的任务引用
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]

    async def cancel_task(self, task_id: str) -> bool:
        """
        取消任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功取消
        """
        async with self._lock:
            if task_id not in self.tasks:
                return False

            task = self.tasks[task_id]

            # 只能取消待处理或运行中的任务
            if task.status not in [TaskStatus.PENDING, TaskStatus.RUNNING]:
                return False

            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.now()

            # 取消异步任务
            if task_id in self.running_tasks:
                self.running_tasks[task_id].cancel()
                del self.running_tasks[task_id]

            return True

    def get_task(self, task_id: str) -> Optional[GenerationTask]:
        """
        获取任务信息

        Args:
            task_id: 任务ID

        Returns:
            任务对象
        """
        return self.tasks.get(task_id)

    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """
        获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务状态字典
        """
        task = self.get_task(task_id)
        if task:
            return task.to_dict()
        return None

    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        列出任务

        Args:
            status: 过滤状态
            limit: 最大数量

        Returns:
            任务列表
        """
        tasks = list(self.tasks.values())

        # 过滤状态
        if status:
            tasks = [t for t in tasks if t.status == status]

        # 按创建时间降序排序
        tasks.sort(key=lambda t: t.created_at, reverse=True)

        # 限制数量
        tasks = tasks[:limit]

        return [t.to_dict() for t in tasks]

    def register_running_task(self, task_id: str, async_task: asyncio.Task) -> None:
        """
        注册运行中的异步任务

        Args:
            task_id: 任务ID
            async_task: 异步任务对象
        """
        self.running_tasks[task_id] = async_task

    def cleanup_old_tasks(self, max_age_hours: int = 24) -> int:
        """
        清理旧任务

        Args:
            max_age_hours: 最大保留时间（小时）

        Returns:
            清理的任务数量
        """
        now = datetime.now()
        to_remove = []

        for task_id, task in self.tasks.items():
            age = (now - task.created_at).total_seconds() / 3600

            if age > max_age_hours and task.status in [
                TaskStatus.COMPLETED,
                TaskStatus.FAILED,
                TaskStatus.CANCELLED
            ]:
                to_remove.append(task_id)

        for task_id in to_remove:
            del self.tasks[task_id]

        return len(to_remove)

    def get_statistics(self) -> Dict:
        """
        获取整体统计信息

        Returns:
            统计信息字典
        """
        total = len(self.tasks)
        status_counts = {}

        for task in self.tasks.values():
            status_name = task.status.value
            status_counts[status_name] = status_counts.get(status_name, 0) + 1

        return {
            "total_tasks": total,
            "status_counts": status_counts,
            "running_count": len(self.running_tasks)
        }

    def __repr__(self) -> str:
        return f"TaskManager(tasks={len(self.tasks)}, running={len(self.running_tasks)})"
