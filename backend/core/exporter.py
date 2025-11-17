"""
导出器模块
负责将验证通过的样本导出为指定格式
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from .utils import setup_logger, save_jsonl, save_json, ensure_dir, chunks


class Exporter:
    """数据导出器"""

    def __init__(self, output_dir: str):
        """
        初始化导出器

        Args:
            output_dir: 输出目录
        """
        self.output_dir = output_dir
        self.logger = setup_logger("Exporter")
        ensure_dir(output_dir)

    def export_to_jsonl(
        self,
        samples: List[Dict],
        filename: str = "data_dpo.jsonl",
        batch_size: int = 1000
    ) -> List[str]:
        """
        导出为JSONL格式

        Args:
            samples: 样本列表
            filename: 文件名
            batch_size: 每个文件的样本数量

        Returns:
            生成的文件路径列表
        """
        if not samples:
            self.logger.warning("没有样本可导出")
            return []

        # 分批
        batches = chunks(samples, batch_size)
        file_paths = []

        for i, batch in enumerate(batches, 1):
            # 生成文件名
            if len(batches) > 1:
                base_name = filename.replace(".jsonl", f"_{i:05d}.jsonl")
            else:
                base_name = filename

            file_path = Path(self.output_dir) / base_name

            # 过滤并格式化样本
            formatted_samples = []
            for sample in batch:
                formatted = {
                    "system": sample.get("system", ""),
                    "tools": sample.get("tools", ""),
                    "messages": sample.get("messages", []),
                    "chosen": sample.get("chosen", ""),
                    "rejected": sample.get("rejected", "")
                }
                formatted_samples.append(formatted)

            # 保存
            save_jsonl(formatted_samples, str(file_path))
            file_paths.append(str(file_path))

            self.logger.info(f"已导出 {len(batch)} 条样本到: {file_path}")

        return file_paths

    def generate_dataset_info(
        self,
        dataset_name: str = "tool_dpo_dataset",
        file_name: str = "data_dpo.jsonl",
        config: Optional[Dict] = None
    ) -> str:
        """
        生成dataset_info.json

        Args:
            dataset_name: 数据集名称
            file_name: 数据文件名
            config: 生成配置（可选）

        Returns:
            dataset_info.json文件路径
        """
        dataset_info = {
            dataset_name: {
                "file_name": file_name,
                "ranking": True,
                "formatting": "sharegpt",
                "columns": {
                    "system": "system",
                    "tools": "tools",
                    "messages": "messages",
                    "chosen": "chosen",
                    "rejected": "rejected"
                }
            }
        }

        # 添加元数据（过滤敏感信息）
        if config:
            # 创建配置副本并移除敏感信息
            safe_config = {k: v for k, v in config.items() if k not in ['api_key', 'password', 'secret', 'token']}
            dataset_info[dataset_name]["metadata"] = {
                "generated_at": datetime.now().isoformat(),
                "config": safe_config
            }

        # 保存
        file_path = Path(self.output_dir) / "dataset_info.json"
        save_json(dataset_info, str(file_path))

        self.logger.info(f"dataset_info.json已生成: {file_path}")
        return str(file_path)

    def export_statistics(self, stats: Dict, filename: str = "generation_stats.json") -> str:
        """
        导出统计信息

        Args:
            stats: 统计数据
            filename: 文件名

        Returns:
            文件路径
        """
        file_path = Path(self.output_dir) / filename
        save_json(stats, str(file_path))

        self.logger.info(f"统计信息已导出: {file_path}")
        return str(file_path)

    def export_invalid_samples(
        self,
        invalid_samples: List[Dict],
        filename: str = "invalid_samples.jsonl"
    ) -> str:
        """
        导出无效样本（用于调试）

        Args:
            invalid_samples: 无效样本列表
            filename: 文件名

        Returns:
            文件路径
        """
        if not invalid_samples:
            return ""

        file_path = Path(self.output_dir) / filename
        save_jsonl(invalid_samples, str(file_path))

        self.logger.info(f"无效样本已导出: {file_path} (共{len(invalid_samples)}条)")
        return str(file_path)

    def create_batch_files(
        self,
        samples: List[Dict],
        batch_size: int = 1000,
        prefix: str = "data_dpo"
    ) -> List[str]:
        """
        创建分批文件

        Args:
            samples: 样本列表
            batch_size: 每批大小
            prefix: 文件名前缀

        Returns:
            文件路径列表
        """
        return self.export_to_jsonl(samples, f"{prefix}.jsonl", batch_size)

    def get_export_summary(self, file_paths: List[str]) -> Dict:
        """
        获取导出摘要

        Args:
            file_paths: 导出的文件路径列表

        Returns:
            摘要信息
        """
        total_size = 0
        file_info = []

        for path in file_paths:
            if Path(path).exists():
                size = Path(path).stat().st_size
                total_size += size

                # 统计行数
                with open(path, 'r', encoding='utf-8') as f:
                    line_count = sum(1 for _ in f)

                file_info.append({
                    "path": path,
                    "size_bytes": size,
                    "size_mb": round(size / (1024 * 1024), 2),
                    "line_count": line_count
                })

        return {
            "file_count": len(file_paths),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "files": file_info
        }

    def __repr__(self) -> str:
        return f"Exporter(output_dir={self.output_dir})"
