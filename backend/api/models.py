"""
API数据模型
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from enum import Enum


class ToolCountMode(str, Enum):
    """工具数量模式"""
    SINGLE = "single"
    RANGE = "range"


class GenerationConfig(BaseModel):
    """生成配置"""
    num_samples: int = Field(default=1000, ge=1, le=100000, description="生成样本数量")
    multi_ratio: float = Field(default=0.3, ge=0.0, le=1.0, description="多轮对话比例")
    tool_count: int = Field(default=3, ge=1, le=20, description="工具数量")
    tool_count_mode: ToolCountMode = Field(default=ToolCountMode.SINGLE, description="工具数量模式")
    tool_count_min: int = Field(default=2, ge=1, le=10, description="工具数量最小值")
    tool_count_max: int = Field(default=5, ge=1, le=20, description="工具数量最大值")
    concurrency: int = Field(default=10, ge=1, le=100, description="并发数")
    tool_list_path: str = Field(default="configs/tools_registry.json", description="工具列表路径")
    base_model: str = Field(default="deepseek-chat", description="基础模型")
    model_api_url: str = Field(default="https://api.deepseek.com", description="API地址")
    api_key: Optional[str] = Field(default=None, description="API密钥")
    output_dir: str = Field(default="data/processed", description="输出目录")
    batch_size: int = Field(default=1000, ge=100, le=10000, description="批次大小")
    seed: Optional[int] = Field(default=None, description="随机种子")
    auto_correction: bool = Field(default=False, description="自动修正")
    strict_validation: bool = Field(default=False, description="严格验证")


class TaskCreateResponse(BaseModel):
    """任务创建响应"""
    task_id: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str
    status: str
    progress: float
    stats: Dict
    output_files: List[str] = []
    error_message: Optional[str] = None
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class LogMessage(BaseModel):
    """日志消息"""
    level: str
    message: str
    timestamp: str


class StatsUpdate(BaseModel):
    """统计更新"""
    progress: float
    completed: int
    total: int
    rate: float
    single_turn: int
    multi_turn: int
    validation_success_rate: float
    errors: List[str] = []
