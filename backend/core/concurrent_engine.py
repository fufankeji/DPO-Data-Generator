"""
并发引擎模块
负责高并发任务执行和进度监控
"""

import asyncio
import time
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from .task_generator import Task
from .data_synthesizer import DataSynthesizer
from .validator import Validator
from .utils import setup_logger


@dataclass
class ProgressStats:
    """进度统计"""
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    single_turn_count: int = 0
    multi_turn_count: int = 0
    validation_success: int = 0
    validation_failed: int = 0
    start_time: float = field(default_factory=time.time)
    errors: List[str] = field(default_factory=list)

    @property
    def progress_percent(self) -> float:
        """进度百分比"""
        if self.total_tasks == 0:
            return 0
        return (self.completed_tasks / self.total_tasks) * 100

    @property
    def generation_rate(self) -> float:
        """生成速率（样本/秒）"""
        elapsed = time.time() - self.start_time
        if elapsed == 0:
            return 0
        return self.completed_tasks / elapsed

    @property
    def validation_success_rate(self) -> float:
        """验证成功率"""
        total_validated = self.validation_success + self.validation_failed
        if total_validated == 0:
            return 0
        return (self.validation_success / total_validated) * 100

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "total": self.total_tasks,
            "completed_count": self.completed_tasks,
            "failed_count": self.failed_tasks,
            "progress_percent": round(self.progress_percent, 2),
            "rate": round(self.generation_rate, 2),
            "single_turn_count": self.single_turn_count,
            "multi_turn_count": self.multi_turn_count,
            "validation_success_rate": round(self.validation_success_rate, 2),
            "errors": self.errors[-10:]  # 只保留最近10条错误
        }


class ConcurrentEngine:
    """并发执行引擎"""

    def __init__(
        self,
        synthesizer: DataSynthesizer,
        validator: Validator,
        concurrency: int = 10
    ):
        """
        初始化并发引擎

        Args:
            synthesizer: 数据合成器
            validator: 验证器
            concurrency: 并发数
        """
        self.synthesizer = synthesizer
        self.validator = validator
        self.concurrency = concurrency
        self.stats = ProgressStats()
        self.logger = setup_logger("ConcurrentEngine")
        self._progress_callbacks: List[Callable] = []
        self._log_callbacks: List[Callable] = []

    def add_progress_callback(self, callback: Callable[[ProgressStats], None]) -> None:
        """添加进度回调函数"""
        self._progress_callbacks.append(callback)

    def add_log_callback(self, callback: Callable[[str], None]) -> None:
        """添加日志回调函数"""
        self._log_callbacks.append(callback)

    async def process_tasks(
        self,
        tasks: List[Task],
        enable_validation: bool = True,
        enable_correction: bool = False
    ) -> tuple[List[Dict], List[Dict]]:
        """
        并发处理任务列表

        Args:
            tasks: 任务列表
            enable_validation: 是否启用验证
            enable_correction: 是否启用自动修正

        Returns:
            (有效样本列表, 无效样本列表)
        """
        # 只在第一次调用时初始化stats，避免重置累积的validation计数
        if self.stats.total_tasks == 0:
            self.stats = ProgressStats(total_tasks=len(tasks))
        else:
            # 更新total_tasks但保留validation计数
            self.stats.total_tasks = len(tasks)

        self.logger.info(f"开始并发处理 {len(tasks)} 个任务，并发度={self.concurrency}")
        await self._notify_log(f"开始并发处理 {len(tasks)} 个任务，并发度={self.concurrency}")

        # 创建信号量控制并发
        semaphore = asyncio.Semaphore(self.concurrency)

        # 创建worker任务
        async def worker(task: Task) -> Optional[Dict]:
            async with semaphore:
                return await self._process_single_task(task)

        # 并发执行
        worker_tasks = [worker(task) for task in tasks]
        samples = await asyncio.gather(*worker_tasks, return_exceptions=True)

        # 过滤异常和None
        valid_samples_list = []
        for sample in samples:
            if isinstance(sample, Exception):
                self.logger.error(f"任务执行异常: {str(sample)}")
                self.stats.failed_tasks += 1
            elif sample is not None:
                valid_samples_list.append(sample)

        # 验证
        if enable_validation:
            self.logger.info("开始验证样本...")
            await self._notify_log(f"开始验证 {len(valid_samples_list)} 个样本...")

            valid_samples, invalid_samples = self.validator.validate_batch(valid_samples_list)

            self.stats.validation_success += len(valid_samples)
            self.stats.validation_failed += len(invalid_samples)

            # 验证完成后立即触发回调，更新前端显示
            await self._notify_log(f"验证完成: 有效={len(valid_samples)}, 无效={len(invalid_samples)}")
            self._notify_progress()

            # 尝试修正无效样本
            if enable_correction and invalid_samples:
                self.logger.info(f"尝试修正 {len(invalid_samples)} 个无效样本...")
                corrected_samples = []
                for sample in invalid_samples:
                    corrected = self.validator.auto_correct(sample)
                    if corrected:
                        corrected_samples.append(corrected)

                self.logger.info(f"成功修正 {len(corrected_samples)} 个样本")
                valid_samples.extend(corrected_samples)
                invalid_samples = [s for s in invalid_samples if s not in corrected_samples]

            self.logger.info(f"验证完成：有效 {len(valid_samples)}, 无效 {len(invalid_samples)}")
            return valid_samples, invalid_samples

        return valid_samples_list, []

    async def _process_single_task(self, task: Task) -> Optional[Dict]:
        """
        处理单个任务

        Args:
            task: 任务对象

        Returns:
            生成的样本
        """
        try:
            # 生成样本
            sample = await self.synthesizer.synthesize_sample(task)

            if sample:
                # 更新统计
                self.stats.completed_tasks += 1

                if task.task_type == "single":
                    self.stats.single_turn_count += 1
                else:
                    self.stats.multi_turn_count += 1

                # 触发回调
                self._notify_progress()

                return sample
            else:
                self.stats.failed_tasks += 1
                return None

        except Exception as e:
            self.stats.failed_tasks += 1
            error_msg = f"任务 {task.task_id} 处理失败: {str(e)}"
            self.stats.errors.append(error_msg)
            self.logger.error(error_msg)
            return None

    def _notify_progress(self) -> None:
        """通知进度更新"""
        for callback in self._progress_callbacks:
            try:
                callback(self.stats)
            except Exception as e:
                self.logger.error(f"进度回调执行失败: {str(e)}")

    async def _notify_log(self, message: str) -> None:
        """通知日志更新"""
        for callback in self._log_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(message)
                else:
                    callback(message)
            except Exception as e:
                self.logger.error(f"日志回调执行失败: {str(e)}")

    async def process_in_batches(
        self,
        tasks: List[Task],
        batch_size: int = 100,
        enable_validation: bool = True
    ) -> tuple[List[Dict], List[Dict]]:
        """
        分批处理任务

        Args:
            tasks: 任务列表
            batch_size: 每批大小
            enable_validation: 是否启用验证

        Returns:
            (有效样本列表, 无效样本列表)
        """
        self.logger.info(f"分批处理模式：共 {len(tasks)} 个任务，每批 {batch_size}")

        all_valid_samples = []
        all_invalid_samples = []

        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            self.logger.info(f"处理批次 {i // batch_size + 1}/{(len(tasks) + batch_size - 1) // batch_size}")

            valid_samples, invalid_samples = await self.process_tasks(batch, enable_validation)

            all_valid_samples.extend(valid_samples)
            all_invalid_samples.extend(invalid_samples)

            # 短暂休息，避免API限流
            await asyncio.sleep(1)

        return all_valid_samples, all_invalid_samples

    def get_stats(self) -> Dict:
        """获取当前统计信息"""
        return self.stats.to_dict()

    def reset_stats(self) -> None:
        """重置统计信息"""
        self.stats = ProgressStats()

    def __repr__(self) -> str:
        return f"ConcurrentEngine(concurrency={self.concurrency})"
