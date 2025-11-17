"""
工具注册中心模块
负责加载、管理和采样工具定义
"""

import json
import random
from typing import Dict, List, Optional
from pathlib import Path
from .utils import setup_logger, load_json, validate_json_structure


class Tool:
    """工具定义类"""

    def __init__(
        self,
        name: str,
        description: str,
        parameters: Dict,
        version: str = "v1",
        category: Optional[str] = None
    ):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.version = version
        self.category = category

    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "name": f"{self.name}@{self.version}",
            "description": self.description,
            "parameters": self.parameters
        }

    def to_openai_format(self) -> Dict:
        """转换为OpenAI函数调用格式"""
        return {
            "type": "function",
            "function": {
                "name": f"{self.name}@{self.version}",
                "description": self.description,
                "parameters": self.parameters
            }
        }

    def __repr__(self) -> str:
        return f"Tool(name={self.name}@{self.version}, category={self.category})"


class ToolRegistry:
    """工具注册中心"""

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化工具注册中心

        Args:
            config_path: 工具配置文件路径
        """
        self.logger = setup_logger("ToolRegistry")
        self.tools: List[Tool] = []
        self.tool_dict: Dict[str, Tool] = {}

        if config_path:
            self.load_tools(config_path)

    def load_tools(self, config_path: str) -> None:
        """
        从JSON配置文件加载工具定义

        Args:
            config_path: 配置文件路径
        """
        try:
            if not Path(config_path).exists():
                self.logger.error(f"配置文件不存在: {config_path}")
                return

            data = load_json(config_path)

            # 支持两种格式：列表或字典
            if isinstance(data, list):
                tools_data = data
            elif isinstance(data, dict) and "tools" in data:
                tools_data = data["tools"]
            else:
                self.logger.error("配置文件格式错误")
                return

            for tool_data in tools_data:
                if not validate_json_structure(tool_data, ["name", "description", "parameters"]):
                    self.logger.warning(f"工具定义缺少必需字段，跳过: {tool_data.get('name', 'unknown')}")
                    continue

                tool = Tool(
                    name=tool_data["name"],
                    description=tool_data["description"],
                    parameters=tool_data["parameters"],
                    version=tool_data.get("version", "v1"),
                    category=tool_data.get("category")
                )

                self.tools.append(tool)
                tool_key = f"{tool.name}@{tool.version}"
                self.tool_dict[tool_key] = tool

            self.logger.info(f"成功加载 {len(self.tools)} 个工具")

        except Exception as e:
            self.logger.error(f"加载工具配置失败: {str(e)}")
            raise

    def get_tool(self, name: str, version: str = "v1") -> Optional[Tool]:
        """
        根据名称和版本获取工具

        Args:
            name: 工具名称
            version: 工具版本

        Returns:
            工具对象，如果不存在则返回None
        """
        tool_key = f"{name}@{version}"
        return self.tool_dict.get(tool_key)

    def sample_tools(
        self,
        n: int,
        category: Optional[str] = None,
        seed: Optional[int] = None
    ) -> List[Tool]:
        """
        随机采样工具

        Args:
            n: 采样数量
            category: 工具类别过滤
            seed: 随机种子

        Returns:
            工具列表
        """
        if seed is not None:
            random.seed(seed)

        # 过滤工具
        available_tools = self.tools
        if category:
            available_tools = [t for t in self.tools if t.category == category]

        if not available_tools:
            self.logger.warning("没有可用的工具")
            return []

        # 采样
        sample_size = min(n, len(available_tools))
        sampled = random.sample(available_tools, sample_size)

        self.logger.debug(f"采样了 {sample_size} 个工具")
        return sampled

    def get_all_tools(self) -> List[Tool]:
        """获取所有工具"""
        return self.tools.copy()

    def get_tools_by_category(self, category: str) -> List[Tool]:
        """根据类别获取工具"""
        return [t for t in self.tools if t.category == category]

    def get_tool_count(self) -> int:
        """获取工具总数"""
        return len(self.tools)

    def validate_tool_schema(self, tool_data: Dict) -> bool:
        """
        验证工具schema是否合法

        Args:
            tool_data: 工具数据字典

        Returns:
            是否合法
        """
        required_keys = ["name", "description", "parameters"]
        if not validate_json_structure(tool_data, required_keys):
            return False

        # 验证parameters结构
        params = tool_data["parameters"]
        if not isinstance(params, dict):
            return False

        if "type" not in params or params["type"] != "object":
            return False

        if "properties" not in params or not isinstance(params["properties"], dict):
            return False

        return True

    def export_tools_json(self, output_path: str) -> None:
        """导出工具定义为JSON格式"""
        tools_data = [tool.to_dict() for tool in self.tools]
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(tools_data, f, ensure_ascii=False, indent=2)
        self.logger.info(f"工具定义已导出到: {output_path}")

    def __len__(self) -> int:
        return len(self.tools)

    def __repr__(self) -> str:
        return f"ToolRegistry(tools={len(self.tools)})"
