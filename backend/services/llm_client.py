"""
LLM客户端模块
封装对各种大模型API的调用
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Optional, Any
import sys
import os
# Add parent directory to path to import core module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.utils import setup_logger


class LLMClient:
    """大模型客户端，支持OpenAI兼容的API"""

    def __init__(
        self,
        api_url: str = "https://api.openai.com/v1",
        api_key: Optional[str] = None,
        model: str = "gpt-3.5-turbo",
        timeout: int = 60,
        max_retries: int = 3
    ):
        """
        初始化LLM客户端

        Args:
            api_url: API地址
            api_key: API密钥
            model: 模型名称
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.logger = setup_logger("LLMClient")

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stop: Optional[List[str]] = None,
        tools: Optional[List[Dict]] = None,
        **kwargs
    ) -> Optional[str]:
        """
        调用chat completion API

        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            stop: 停止词列表
            tools: 工具列表（OpenAI格式）
            **kwargs: 其他参数

        Returns:
            模型回复内容
        """
        headers = {
            "Content-Type": "application/json"
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            **kwargs
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        if stop:
            payload["stop"] = stop

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        for attempt in range(self.max_retries):
            try:
                request_url = f"{self.api_url}/chat/completions"
                self.logger.info(f"发送请求到: {request_url}, 模型: {self.model}")

                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        request_url,
                        headers=headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=self.timeout)
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            content = result["choices"][0]["message"]["content"]
                            return content
                        else:
                            error_text = await response.text()
                            self.logger.error(f"API请求失败 (状态码 {response.status}): {error_text}")

                            if response.status >= 500:
                                # 服务器错误，重试
                                if attempt < self.max_retries - 1:
                                    await asyncio.sleep(2 ** attempt)
                                    continue
                            else:
                                # 客户端错误，不重试
                                return None

            except asyncio.TimeoutError:
                self.logger.warning(f"请求超时 (尝试 {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue

            except Exception as e:
                self.logger.error(f"请求异常: {str(e)}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue

        self.logger.error(f"达到最大重试次数，请求失败")
        return None

    async def generate_function_call(
        self,
        user_query: str,
        system_prompt: str,
        tools_json: str,
        temperature: float = 0.7
    ) -> Optional[str]:
        """
        生成函数调用

        Args:
            user_query: 用户问题
            system_prompt: 系统提示词
            tools_json: 工具定义JSON字符串
            temperature: 温度参数

        Returns:
            模型回复（包含function_call标签）
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"可用工具列表：\n{tools_json}\n\n用户问题：{user_query}"}
        ]

        response = await self.chat_completion(messages, temperature=temperature)
        return response

    async def generate_chosen_response(
        self,
        user_query: str,
        system_prompt: str,
        tools_json: str,
        temperature: float = 0.7
    ) -> Optional[str]:
        """
        生成正确的回复（chosen）

        Args:
            user_query: 用户问题
            system_prompt: 系统提示词
            tools_json: 工具定义JSON字符串
            temperature: 温度参数

        Returns:
            正确的回复
        """
        # 添加明确的指令
        enhanced_system = system_prompt + "\n\n请务必准确理解用户意图，选择最合适的工具进行调用。"

        messages = [
            {"role": "system", "content": enhanced_system},
            {"role": "user", "content": f"可用工具：\n{tools_json}\n\n请根据以下问题调用合适的工具：{user_query}"}
        ]

        response = await self.chat_completion(messages, temperature=temperature)
        return response

    async def generate_rejected_response(
        self,
        user_query: str,
        system_prompt: str,
        tools_json: str,
        chosen_response: Optional[str] = None,
        conversation_history: Optional[List[Dict]] = None,
        temperature: float = 0.9
    ) -> Optional[str]:
        """
        生成错误的回复（rejected）

        Args:
            user_query: 用户问题（当前轮次）
            system_prompt: 系统提示词
            tools_json: 工具定义JSON字符串
            chosen_response: 正确的回复（可选，用于参考）
            conversation_history: 对话历史（可选，用于多轮对话）
            temperature: 温度参数（较高以增加多样性）

        Returns:
            错误的回复
        """
        # 构造提示，让模型生成一个"不太正确"的回复
        rejection_prompt = f"""
{system_prompt}

现在，请你故意生成一个不太准确或不是最优的回复。可以是：
1. 调用了错误的工具
2. 参数不完整或不准确
3. 调用顺序不合理
4. 忘记调用必要的工具
5. 完全不调用工具（直接回答或拒绝回答）
6. 误解用户意图

不需要保证格式正确，可以有各种形式的错误回复。
"""

        if chosen_response:
            rejection_prompt += f"\n\n正确的回复示例（不要直接复制）：\n{chosen_response}\n\n现在请生成一个\"不太好\"的替代方案。"

        messages = [{"role": "system", "content": rejection_prompt}]

        # 如果有对话历史，加入对话历史
        if conversation_history:
            messages.extend(conversation_history)

        # 添加当前用户问题
        messages.append({"role": "user", "content": f"可用工具：\n{tools_json}\n\n用户问题：{user_query}"})

        response = await self.chat_completion(messages, temperature=temperature)
        return response

    async def validate_and_correct(
        self,
        sample: Dict,
        temperature: float = 0.5
    ) -> Dict:
        """
        验证样本并生成修正版本（增强版：包含相似度评分和质量评分）

        Args:
            sample: 样本数据
            temperature: 温度参数

        Returns:
            包含验证结果和修正版本的字典
            {
                "is_valid": bool,
                "quality_score": float (0-10),
                "similarity_score": float (0-100),
                "issues": List[str],
                "corrected_chosen": str,
                "corrected_rejected": str
            }
        """
        validation_prompt = f"""
请检查以下DPO训练样本的质量：

用户问题：{sample.get('messages', [{}])[0].get('content', '')}
可用工具：{sample.get('tools', '')}
Chosen回复：{sample.get('chosen', '')}
Rejected回复：{sample.get('rejected', '')}

请评估以下方面：

1. **Chosen回复质量** (是否正确调用了工具，参数是否准确)
2. **Rejected回复质量** (是否确实比chosen更差)
3. **两者差异度** (差异是否明显，是否具有学习价值)
4. **格式规范性** (是否符合function_call格式要求)

请以JSON格式回复，必须包含以下字段：
{{
  "is_valid": true/false,  # 样本是否整体合格
  "quality_score": 8.5,  # 0-10分，chosen的质量评分
  "similarity_score": 25.0,  # 0-100，chosen和rejected的相似度百分比（越低越好，<80%为佳）
  "issues": ["问题1", "问题2"],  # 发现的问题列表
  "corrected_chosen": "修正后的chosen（如果需要修正）",  # 没有问题则返回原内容
  "corrected_rejected": "修正后的rejected（如果需要修正）"  # 没有问题则返回原内容
}}

评分标准：
- quality_score: 9-10极好，7-8良好，5-6一般，<5差
- similarity_score: <50%优秀，50-80%良好，>80%需要改进（说明rejected不够差）
"""

        messages = [
            {"role": "system", "content": "你是一个DPO数据质量检查专家，擅长评估偏好对比数据的质量。"},
            {"role": "user", "content": validation_prompt}
        ]

        response = await self.chat_completion(messages, temperature=temperature)

        try:
            if not response:
                return {
                    "is_valid": True,
                    "quality_score": 7.0,
                    "similarity_score": 50.0,
                    "issues": []
                }

            # 清理Markdown代码块包裹（DeepSeek常见问题）
            cleaned_response = response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]  # 移除 ```json
            if cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[3:]  # 移除 ```
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]  # 移除结尾的 ```
            cleaned_response = cleaned_response.strip()

            result = json.loads(cleaned_response)

            # 确保所有必需字段存在
            if "quality_score" not in result:
                result["quality_score"] = 7.0
            if "similarity_score" not in result:
                result["similarity_score"] = 50.0
            if "issues" not in result:
                result["issues"] = []
            if "is_valid" not in result:
                result["is_valid"] = True

            return result
        except json.JSONDecodeError as e:
            self.logger.error(f"无法解析验证结果: {response[:200]}... 错误: {str(e)}")
            return {
                "is_valid": True,
                "quality_score": 7.0,
                "similarity_score": 50.0,
                "issues": ["LLM返回格式错误"]
            }

    async def generate_follow_up_question(
        self,
        conversation_history: List[Dict],
        tools_json: str,
        temperature: float = 0.8
    ) -> Optional[str]:
        """
        生成追问问题（用于多轮对话）

        Args:
            conversation_history: 对话历史
            tools_json: 工具定义JSON字符串
            temperature: 温度参数

        Returns:
            追问问题
        """
        follow_up_prompt = """
根据之前的对话，生成一个合理的追问。追问应该：
1. 与之前的对话内容相关
2. 需要调用工具来回答
3. 是用户可能会问的自然问题

可用工具：
{tools}

请直接生成追问，不要包含其他内容。
"""

        messages = conversation_history.copy()
        messages.append({
            "role": "system",
            "content": follow_up_prompt.format(tools=tools_json)
        })

        response = await self.chat_completion(messages, temperature=temperature, max_tokens=200)
        return response

    async def generate_multi_turn_dialogue(
        self,
        initial_query: str,
        system_prompt: str,
        tools_json: str,
        max_turns: int = 3
    ) -> List[Dict[str, str]]:
        """
        生成多轮对话（最多max_turns轮）

        Args:
            initial_query: 初始问题
            system_prompt: 系统提示词
            tools_json: 工具定义JSON字符串
            max_turns: 最大轮次

        Returns:
            对话历史列表 [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
        """
        conversation = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": initial_query}
        ]

        # 第一轮：回答初始问题
        first_response = await self.generate_chosen_response(
            user_query=initial_query,
            system_prompt=system_prompt,
            tools_json=tools_json
        )

        if not first_response:
            return conversation

        conversation.append({"role": "assistant", "content": first_response})

        # 后续轮次
        for turn in range(1, max_turns):
            # 生成追问
            follow_up = await self.generate_follow_up_question(
                conversation_history=conversation,
                tools_json=tools_json
            )

            if not follow_up:
                break

            conversation.append({"role": "user", "content": follow_up})

            # 回答追问
            follow_up_response = await self.chat_completion(
                messages=conversation,
                temperature=0.7
            )

            if not follow_up_response:
                break

            conversation.append({"role": "assistant", "content": follow_up_response})

        # 移除system message（不需要保存到最终数据中）
        return [msg for msg in conversation if msg["role"] != "system"]

    def set_model(self, model: str) -> None:
        """设置模型"""
        self.model = model
        self.logger.info(f"模型已切换为: {model}")

    def set_api_key(self, api_key: str) -> None:
        """设置API密钥"""
        self.api_key = api_key

    def __repr__(self) -> str:
        return f"LLMClient(model={self.model}, api_url={self.api_url})"
