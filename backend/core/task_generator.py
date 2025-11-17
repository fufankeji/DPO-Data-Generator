"""
任务生成器模块
负责根据工具定义生成自然语言任务和上下文
"""

import random
import json
from typing import Dict, List, Optional, Tuple
from .tool_registry import Tool, ToolRegistry
from .utils import setup_logger, generate_id


class Task:
    """任务定义类"""

    def __init__(
        self,
        task_id: str,
        task_type: str,  # 'single' or 'multi'
        tools: List[Tool],
        user_query: str,
        system_prompt: str,
        expected_tool_sequence: Optional[List[str]] = None
    ):
        self.task_id = task_id
        self.task_type = task_type
        self.tools = tools
        self.user_query = user_query
        self.system_prompt = system_prompt
        self.expected_tool_sequence = expected_tool_sequence or []

    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "system": self.system_prompt,
            "tools": json.dumps([tool.to_dict() for tool in self.tools], ensure_ascii=False),
            "messages": [{"role": "user", "content": self.user_query}],
            "expected_tool_sequence": self.expected_tool_sequence
        }

    def __repr__(self) -> str:
        return f"Task(id={self.task_id}, type={self.task_type}, tools={len(self.tools)})"


class TaskGenerator:
    """任务生成器"""

    # 默认系统提示词
    DEFAULT_SYSTEM_PROMPT = """你是一个智能AI助手，可以通过调用工具来帮助用户完成各种任务。

你需要根据用户的问题，选择合适的工具进行调用。工具调用格式如下：

<function_call>
{
  "name": "工具名称@版本",
  "arguments": {
    "参数名": "参数值"
  }
}
</function_call>

在得到工具返回结果后，你需要用<final>标签给出最终回答：

<final>
这是最终的回答内容
</final>

请确保你的工具调用是准确的，参数是完整的。"""

    # 任务模板（按工具类型分类，增加多样性）
    TASK_TEMPLATES = {
        "天气查询": [
            "请帮我查询{city}的天气情况",
            "{city}今天天气怎么样？",
            "我想知道{city}最近的天气预报",
            "{city}这周末天气如何？",
            "查一下{city}明天会不会下雨",
            "{city}的气温多少度？",
            "帮我看看{city}适不适合出门",
            "{city}未来三天天气怎么样",
            "我要去{city}，需要带伞吗？",
            "{city}现在是什么天气",
            "今天{city}的空气质量怎么样",
            "{city}的温度和湿度是多少"
        ],
        "时间查询": [
            "现在几点了？",
            "请告诉我当前时间",
            "帮我看一下现在的时间",
            "现在是几点几分",
            "当前时间是多少",
            "告诉我准确的时间",
            "几点了",
            "什么时候了",
            "现在的北京时间",
            "时间多少了"
        ],
        "计算": [
            "帮我计算{expr}",
            "{expr}等于多少？",
            "请计算这个表达式：{expr}",
            "算一下{expr}",
            "{expr}的结果是什么",
            "计算{expr}的值",
            "求{expr}",
            "{expr}怎么算",
            "帮我算算{expr}是多少",
            "我想知道{expr}的答案"
        ],
        "搜索": [
            "帮我搜索关于{query}的信息",
            "我想了解一下{query}",
            "请搜索{query}相关内容",
            "查一下{query}",
            "{query}是什么",
            "给我介绍一下{query}",
            "我想知道{query}的详细信息",
            "关于{query}有哪些内容",
            "找一找{query}的资料",
            "搜索{query}相关的文章",
            "{query}有什么特点",
            "告诉我{query}的背景"
        ],
        "翻译": [
            "请把'{text}'翻译成{target_lang}",
            "帮我翻译：{text}，目标语言是{target_lang}",
            "这句话用{target_lang}怎么说：{text}",
            "'{text}'的{target_lang}翻译",
            "翻译{text}为{target_lang}",
            "{text}翻译成{target_lang}怎么说",
            "用{target_lang}说{text}",
            "把{text}转换成{target_lang}",
            "{text}用{target_lang}如何表达",
            "请将{text}译为{target_lang}"
        ],
        "货币转换": [
            "把{amount}{from_currency}转换成{to_currency}",
            "{amount}{from_currency}等于多少{to_currency}",
            "我想知道{amount}{from_currency}的{to_currency}价值",
            "帮我换算{amount}{from_currency}到{to_currency}",
            "{from_currency}兑{to_currency}汇率是多少",
            "{amount}{from_currency}能换多少{to_currency}",
            "转换{amount}{from_currency}为{to_currency}"
        ],
        "新闻获取": [
            "给我看看{category}类的新闻",
            "最近有什么{category}新闻",
            "我想看{category}方面的资讯",
            "帮我找找{category}的最新消息",
            "{category}领域有什么新动态",
            "查看{category}新闻头条",
            "今天的{category}新闻有哪些"
        ],
        "通用": [
            "请使用合适的工具帮我完成这个任务",
            "我需要你的帮助来解决这个问题",
            "请调用相关工具来处理这个请求",
            "帮我用{tool_name}完成任务",
            "可以用工具帮我吗",
            "需要调用什么工具",
            "这个问题怎么处理",
            "请使用{tool_name}工具"
        ]
    }

    # 扩展的参数池，增加多样性
    PARAMS = {
        "cities": ["北京", "上海", "广州", "深圳", "杭州", "成都", "西安", "武汉", "南京", "重庆",
                   "天津", "苏州", "长沙", "青岛", "大连", "厦门", "宁波", "济南", "哈尔滨", "郑州"],
        "expressions": ["1+1", "25*4", "100/5", "2^10", "sqrt(144)", "15-8", "36/6", "7*8",
                       "1000-567", "45+78", "99/3", "12*12", "(10+5)*2", "50%3", "2^8"],
        "search_queries": ["人工智能", "机器学习", "深度学习", "自然语言处理", "大模型", "ChatGPT",
                          "Python编程", "数据科学", "云计算", "区块链", "物联网", "5G技术",
                          "量子计算", "元宇宙", "Web3", "神经网络", "计算机视觉", "语音识别"],
        "texts": ["你好", "谢谢", "再见", "早上好", "晚安", "对不起", "没关系", "请稍等",
                 "很高兴认识你", "今天天气真好", "祝你好运", "生日快乐", "新年快乐"],
        "target_langs": ["英语", "日语", "法语", "德语", "西班牙语", "韩语", "俄语", "阿拉伯语"],
        "currencies_from": ["美元", "人民币", "欧元", "英镑", "日元"],
        "currencies_to": ["人民币", "美元", "欧元", "英镑", "港币"],
        "amounts": [100, 500, 1000, 50, 200, 5000, 10000],
        "news_categories": ["科技", "体育", "财经", "娱乐", "国际", "社会", "军事", "健康"]
    }

    # 多轮对话的连接词
    MULTI_TURN_CONNECTORS = [
        "然后",
        "接着",
        "同时",
        "另外",
        "还有",
        "并且",
        "以及"
    ]

    def __init__(self, tool_registry: ToolRegistry):
        """
        初始化任务生成器

        Args:
            tool_registry: 工具注册中心实例
        """
        self.tool_registry = tool_registry
        self.logger = setup_logger("TaskGenerator")

    def generate_tasks(
        self,
        num_samples: int,
        multi_ratio: float = 0.3,
        tool_count: int = 3,
        tool_count_range: Optional[Tuple[int, int]] = None,
        seed: Optional[int] = None
    ) -> List[Task]:
        """
        批量生成任务

        Args:
            num_samples: 生成任务数量
            multi_ratio: 多轮任务比例 (0-1)
            tool_count: 每个任务使用的工具数量（固定值）
            tool_count_range: 工具数量范围 (min, max)，如果指定则忽略tool_count
            seed: 随机种子

        Returns:
            任务列表
        """
        if seed is not None:
            random.seed(seed)

        tasks = []
        num_multi = int(num_samples * multi_ratio)
        num_single = num_samples - num_multi

        self.logger.info(f"开始生成任务：单轮={num_single}, 多轮={num_multi}")

        # 生成单轮任务
        for i in range(num_single):
            if tool_count_range:
                n_tools = random.randint(tool_count_range[0], tool_count_range[1])
            else:
                n_tools = tool_count

            task = self.generate_single_turn_task(n_tools=n_tools)
            if task:
                tasks.append(task)

        # 生成多轮任务
        for i in range(num_multi):
            if tool_count_range:
                n_tools = random.randint(tool_count_range[0], tool_count_range[1])
            else:
                n_tools = tool_count

            task = self.generate_multi_turn_task(n_tools=n_tools)
            if task:
                tasks.append(task)

        self.logger.info(f"任务生成完成：共 {len(tasks)} 个")
        return tasks

    def generate_single_turn_task(
        self,
        n_tools: int = 3,
        system_prompt: Optional[str] = None
    ) -> Optional[Task]:
        """
        生成单轮调用任务

        Args:
            n_tools: 可用工具数量
            system_prompt: 自定义系统提示词

        Returns:
            任务对象
        """
        # 采样工具
        tools = self.tool_registry.sample_tools(n_tools)
        if not tools:
            self.logger.warning("无法采样工具，跳过任务生成")
            return None

        # 随机选择一个工具作为目标
        target_tool = random.choice(tools)

        # 生成自然语言问题
        user_query = self._generate_query_for_tool(target_tool)

        # 创建任务
        task_id = generate_id("task")
        task = Task(
            task_id=task_id,
            task_type="single",
            tools=tools,
            user_query=user_query,
            system_prompt=system_prompt or self.DEFAULT_SYSTEM_PROMPT,
            expected_tool_sequence=[f"{target_tool.name}@{target_tool.version}"]
        )

        return task

    def generate_multi_turn_task(
        self,
        n_tools: int = 3,
        system_prompt: Optional[str] = None
    ) -> Optional[Task]:
        """
        生成多轮调用任务

        Args:
            n_tools: 可用工具数量
            system_prompt: 自定义系统提示词

        Returns:
            任务对象
        """
        # 采样工具
        tools = self.tool_registry.sample_tools(n_tools)
        if not tools or len(tools) < 2:
            self.logger.warning("工具数量不足，无法生成多轮任务")
            return None

        # 随机选择2-3个工具作为目标序列
        num_steps = min(random.randint(2, 3), len(tools))
        target_tools = random.sample(tools, num_steps)

        # 生成组合问题
        user_query = self._generate_multi_turn_query(target_tools)

        # 创建任务
        task_id = generate_id("task")
        task = Task(
            task_id=task_id,
            task_type="multi",
            tools=tools,
            user_query=user_query,
            system_prompt=system_prompt or self.DEFAULT_SYSTEM_PROMPT,
            expected_tool_sequence=[f"{t.name}@{t.version}" for t in target_tools]
        )

        return task

    def _generate_query_for_tool(self, tool: Tool) -> str:
        """为单个工具生成自然语言问题（增强多样性）"""
        tool_name = tool.name.lower()
        tool_desc = tool.description.lower()

        # 根据工具名称和描述推断类别
        if "weather" in tool_name or "天气" in tool_name or "天气" in tool_desc:
            template = random.choice(self.TASK_TEMPLATES["天气查询"])
            return template.format(city=random.choice(self.PARAMS["cities"]))

        elif "time" in tool_name or "时间" in tool_name or "clock" in tool_name:
            template = random.choice(self.TASK_TEMPLATES["时间查询"])
            return template

        elif "calc" in tool_name or "计算" in tool_name or "math" in tool_name:
            template = random.choice(self.TASK_TEMPLATES["计算"])
            return template.format(expr=random.choice(self.PARAMS["expressions"]))

        elif "search" in tool_name or "搜索" in tool_name or "查询" in tool_desc:
            template = random.choice(self.TASK_TEMPLATES["搜索"])
            return template.format(query=random.choice(self.PARAMS["search_queries"]))

        elif "translate" in tool_name or "翻译" in tool_name:
            template = random.choice(self.TASK_TEMPLATES["翻译"])
            return template.format(
                text=random.choice(self.PARAMS["texts"]),
                target_lang=random.choice(self.PARAMS["target_langs"])
            )

        elif "currency" in tool_name or "convert" in tool_name or "汇率" in tool_name or "货币" in tool_desc:
            template = random.choice(self.TASK_TEMPLATES["货币转换"])
            return template.format(
                amount=random.choice(self.PARAMS["amounts"]),
                from_currency=random.choice(self.PARAMS["currencies_from"]),
                to_currency=random.choice(self.PARAMS["currencies_to"])
            )

        elif "news" in tool_name or "新闻" in tool_name or "资讯" in tool_desc:
            template = random.choice(self.TASK_TEMPLATES["新闻获取"])
            return template.format(category=random.choice(self.PARAMS["news_categories"]))

        else:
            # 通用模板：基于工具描述生成
            template = random.choice(self.TASK_TEMPLATES["通用"])
            if "{tool_name}" in template:
                return template.format(tool_name=tool.description)
            else:
                return f"请使用{tool.description}的功能帮我完成任务"

    def _generate_multi_turn_query(self, tools: List[Tool]) -> str:
        """为多个工具生成组合问题"""
        queries = []
        for tool in tools:
            query = self._generate_query_for_tool(tool)
            queries.append(query)

        # 使用连接词连接
        if len(queries) == 2:
            connector = random.choice(self.MULTI_TURN_CONNECTORS)
            return f"{queries[0]}，{connector}{queries[1]}"
        else:
            # 3个或更多
            combined = queries[0]
            for i, query in enumerate(queries[1:], 1):
                if i == len(queries) - 1:
                    combined += f"，最后{query}"
                else:
                    connector = random.choice(self.MULTI_TURN_CONNECTORS)
                    combined += f"，{connector}{query}"
            return combined

    def create_custom_task(
        self,
        user_query: str,
        tool_names: List[str],
        task_type: str = "single",
        system_prompt: Optional[str] = None
    ) -> Optional[Task]:
        """
        创建自定义任务

        Args:
            user_query: 用户问题
            tool_names: 工具名称列表（格式：name@version 或 name）
            task_type: 任务类型
            system_prompt: 系统提示词

        Returns:
            任务对象
        """
        tools = []
        for tool_name in tool_names:
            if "@" in tool_name:
                name, version = tool_name.split("@")
                tool = self.tool_registry.get_tool(name, version)
            else:
                tool = self.tool_registry.get_tool(tool_name)

            if tool:
                tools.append(tool)
            else:
                self.logger.warning(f"工具不存在: {tool_name}")

        if not tools:
            self.logger.error("没有有效的工具")
            return None

        task_id = generate_id("task")
        task = Task(
            task_id=task_id,
            task_type=task_type,
            tools=tools,
            user_query=user_query,
            system_prompt=system_prompt or self.DEFAULT_SYSTEM_PROMPT
        )

        return task
