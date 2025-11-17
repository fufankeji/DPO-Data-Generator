"""
工具函数模块
提供通用的辅助函数
"""

import json
import random
import hashlib
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path


def setup_logger(name: str, log_file: Optional[str] = None, level=logging.INFO) -> logging.Logger:
    """设置日志记录器"""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    formatter = logging.Formatter(
        '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件处理器
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def load_json(file_path: str) -> Any:
    """加载JSON文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data: Any, file_path: str, indent: int = 2) -> None:
    """保存JSON文件"""
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)


def save_jsonl(data: List[Dict], file_path: str, pretty: bool = True) -> None:
    """
    保存JSONL文件（每行一个JSON对象）

    Args:
        data: 数据列表
        file_path: 文件路径
        pretty: 是否格式化输出（默认True，输出带缩进的格式化JSON）
    """
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        for item in data:
            if pretty:
                f.write(json.dumps(item, ensure_ascii=False, indent=2) + '\n')
            else:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')


def load_jsonl(file_path: str) -> List[Dict]:
    """加载JSONL文件"""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data


def generate_id(prefix: str = "task") -> str:
    """生成唯一ID"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_suffix = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=6))
    return f"{prefix}_{timestamp}_{random_suffix}"


def compute_hash(text: str) -> str:
    """计算文本的哈希值"""
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def truncate_text(text: str, max_length: int = 100) -> str:
    """截断文本"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def format_time(seconds: float) -> str:
    """格式化时间"""
    if seconds < 60:
        return f"{seconds:.1f}秒"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}分钟"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}小时"


def validate_json_structure(data: Dict, required_keys: List[str]) -> bool:
    """验证JSON结构是否包含必需的键"""
    return all(key in data for key in required_keys)


def safe_get(data: Dict, key: str, default: Any = None) -> Any:
    """安全获取字典值"""
    return data.get(key, default)


def chunks(lst: List, n: int) -> List[List]:
    """将列表分成固定大小的块"""
    return [lst[i:i + n] for i in range(0, len(lst), n)]


def ensure_dir(path: str) -> None:
    """确保目录存在"""
    Path(path).mkdir(parents=True, exist_ok=True)


def count_tokens_approximate(text: str) -> int:
    """粗略估算token数量（中文按2个字符=1token，英文按4个字符=1token）"""
    chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
    other_chars = len(text) - chinese_chars
    return chinese_chars // 2 + other_chars // 4


def merge_dicts(dict1: Dict, dict2: Dict) -> Dict:
    """合并两个字典，dict2的值会覆盖dict1的值"""
    result = dict1.copy()
    result.update(dict2)
    return result
