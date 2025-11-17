"""
数据合成器模块
负责调用LLM生成DPO训练样本（chosen和rejected）
"""

import asyncio
from typing import Dict, Optional, Tuple, List
from core.task_generator import Task
from services.llm_client import LLMClient
from core.utils import setup_logger


class DataSynthesizer:
    """数据合成器（增强版：智能rejected策略）"""

    def __init__(self, llm_client: LLMClient, enable_smart_rejected: bool = True):
        """
        初始化数据合成器

        Args:
            llm_client: LLM客户端实例
            enable_smart_rejected: 是否启用智能rejected策略
        """
        self.llm_client = llm_client
        self.enable_smart_rejected = enable_smart_rejected
        self.logger = setup_logger("DataSynthesizer")

    async def synthesize_sample(
        self,
        task: Task,
        enable_step2: bool = False
    ) -> Optional[Dict]:
        """
        合成DPO样本（增强版：智能rejected策略）

        Args:
            task: 任务对象
            enable_step2: 是否启用Step2（生成观察后的回答）

        Returns:
            DPO样本字典
        """
        try:
            if self.enable_smart_rejected:
                # 使用智能rejected策略
                return await self.synthesize_sample_with_smart_rejected(task)
            else:
                # 使用原始策略
                return await self._synthesize_sample_basic(task)

        except Exception as e:
            self.logger.error(f"样本合成异常: {str(e)}")
            return None

    async def _synthesize_sample_basic(self, task: Task) -> Optional[Dict]:
        """
        基础样本生成（原始策略）

        Args:
            task: 任务对象

        Returns:
            DPO样本字典
        """
        # 并发生成chosen和rejected
        chosen_task = self._generate_chosen(task)
        rejected_task = self._generate_rejected(task)

        chosen, rejected = await asyncio.gather(chosen_task, rejected_task)

        if not chosen or not rejected:
            self.logger.warning(f"样本生成失败: task_id={task.task_id}")
            return None

        # 构造DPO样本
        sample = {
            "task_id": task.task_id,
            "task_type": task.task_type,
            "system": task.system_prompt,
            "tools": task.to_dict()["tools"],
            "messages": task.to_dict()["messages"],
            "chosen": chosen,
            "rejected": rejected
        }

        self.logger.debug(f"样本生成成功: task_id={task.task_id}")
        return sample

    async def synthesize_sample_with_smart_rejected(self, task: Task) -> Optional[Dict]:
        """
        智能rejected策略生成样本

        策略：
        1. 生成chosen (正确版本)
        2. 生成rejected (故意出错版本)
        3. 使用LLM自评检查质量
        4. 如果rejected有格式错误 → 修正后作为新chosen，原错误作为rejected
        5. 如果rejected相似度>80% → 重新生成更差的版本

        Args:
            task: 任务对象

        Returns:
            DPO样本字典
        """
        # 第一步：并发生成chosen和rejected
        chosen_task = self._generate_chosen(task)
        rejected_task = self._generate_rejected(task)

        chosen, rejected = await asyncio.gather(chosen_task, rejected_task)

        if not chosen or not rejected:
            self.logger.warning(f"样本生成失败: task_id={task.task_id}")
            return None

        # 第二步：构造临时样本用于验证
        temp_sample = {
            "task_id": task.task_id,
            "task_type": task.task_type,
            "system": task.system_prompt,
            "tools": task.to_dict()["tools"],
            "messages": task.to_dict()["messages"],
            "chosen": chosen,
            "rejected": rejected
        }

        # 第三步：LLM自评验证
        llm_result = await self.llm_client.validate_and_correct(temp_sample)

        quality_score = llm_result.get("quality_score", 7.0)
        similarity_score = llm_result.get("similarity_score", 50.0)

        self.logger.info(f"样本{task.task_id}质量评分: {quality_score}/10, 相似度: {similarity_score}%")

        # 第四步：智能策略处理
        final_chosen = chosen
        final_rejected = rejected

        # 策略1: 如果rejected质量太差（可能有格式错误），尝试修正
        if quality_score < 5.0 and llm_result.get("corrected_chosen"):
            corrected_chosen = llm_result.get("corrected_chosen")
            if corrected_chosen and corrected_chosen != chosen:
                self.logger.info(f"样本{task.task_id}: 使用修正后的chosen，原rejected作为真实错误案例")
                final_chosen = corrected_chosen
                # rejected保持原样（作为真实错误案例）

        # 策略2: 如果相似度过高(>80%)，重新生成更差的rejected
        if similarity_score > 80.0:
            self.logger.warning(f"样本{task.task_id}: rejected相似度过高({similarity_score}%)，重新生成")

            # 获取对话上下文
            conversation_history = getattr(task, '_multi_turn_context', None)

            # 确定当前用户问题
            if conversation_history and len(conversation_history) > 0:
                current_query = None
                for msg in reversed(conversation_history):
                    if msg["role"] == "user":
                        current_query = msg["content"]
                        break
                if not current_query:
                    current_query = task.user_query
            else:
                current_query = task.user_query

            # 使用更高的温度和明确的提示重新生成
            regenerated_rejected = await self.llm_client.generate_rejected_response(
                user_query=current_query,
                system_prompt=task.system_prompt,
                tools_json=task.to_dict()["tools"],
                conversation_history=conversation_history,
                chosen_response=final_chosen,
                temperature=1.2  # 更高的温度
            )

            if regenerated_rejected:
                final_rejected = regenerated_rejected
                self.logger.info(f"样本{task.task_id}: rejected重新生成成功")

        # 第五步：构造最终样本
        # 如果是多轮对话，使用完整的对话历史；否则使用原始messages
        if hasattr(task, '_multi_turn_context') and task._multi_turn_context:
            messages = task._multi_turn_context
        else:
            messages = task.to_dict()["messages"]

        final_sample = {
            "task_id": task.task_id,
            "task_type": task.task_type,
            "system": task.system_prompt,
            "tools": task.to_dict()["tools"],
            "messages": messages,
            "chosen": final_chosen,
            "rejected": final_rejected,
            "quality_score": quality_score,
            "similarity_score": similarity_score
        }

        self.logger.debug(f"智能样本生成成功: task_id={task.task_id}")
        return final_sample

    async def _generate_chosen(self, task: Task) -> Optional[str]:
        """
        生成正确的回复（chosen）- 支持多轮对话

        对于多轮对话：
        - 生成完整对话历史
        - 将对话历史更新到task.messages（除了最后一条assistant回复）
        - 返回最后一条assistant回复作为chosen

        对于单轮对话：
        - 直接返回assistant回复
        """
        try:
            # 如果是多轮对话任务
            if task.task_type == "multi":
                dialogue = await self.llm_client.generate_multi_turn_dialogue(
                    initial_query=task.user_query,
                    system_prompt=task.system_prompt,
                    tools_json=task.to_dict()["tools"],
                    max_turns=3  # 最多3轮
                )

                if dialogue and len(dialogue) > 0:
                    # 找到最后一条assistant回复
                    last_assistant_reply = None
                    for msg in reversed(dialogue):
                        if msg["role"] == "assistant":
                            last_assistant_reply = msg["content"]
                            break

                    if last_assistant_reply:
                        # 更新task的messages为除了最后一条assistant回复之外的所有消息
                        # 这样rejected生成时可以看到完整的对话上下文
                        conversation_context = []
                        for msg in dialogue:
                            if msg["role"] in ["user", "assistant"]:
                                conversation_context.append(msg)
                                if msg["role"] == "assistant" and msg["content"] == last_assistant_reply:
                                    # 找到最后一条assistant回复，移除它
                                    conversation_context.pop()
                                    break

                        # 更新task的messages字段（用于后续构造样本）
                        task._multi_turn_context = conversation_context

                        self.logger.info(f"多轮对话生成成功: {task.task_id}, 共{len(conversation_context)+1}条消息")
                        return last_assistant_reply
                    else:
                        self.logger.warning(f"多轮对话中未找到assistant回复，回退到单轮: {task.task_id}")
                else:
                    # 如果多轮对话生成失败，回退到单轮
                    self.logger.warning(f"多轮对话生成失败，回退到单轮: {task.task_id}")

            # 单轮对话
            response = await self.llm_client.generate_chosen_response(
                user_query=task.user_query,
                system_prompt=task.system_prompt,
                tools_json=task.to_dict()["tools"],
                temperature=0.7
            )
            return response
        except Exception as e:
            self.logger.error(f"生成chosen失败: {str(e)}")
            return None

    async def _generate_rejected(self, task: Task) -> Optional[str]:
        """
        生成错误的回复（rejected）

        支持多轮对话：如果task有_multi_turn_context，会将对话历史传递给LLM
        """
        try:
            # 获取对话上下文（如果是多轮对话）
            conversation_history = getattr(task, '_multi_turn_context', None)

            # 确定当前轮次的用户问题
            if conversation_history and len(conversation_history) > 0:
                # 多轮对话：获取最后一条用户消息
                current_query = None
                for msg in reversed(conversation_history):
                    if msg["role"] == "user":
                        current_query = msg["content"]
                        break

                if not current_query:
                    current_query = task.user_query
            else:
                # 单轮对话
                current_query = task.user_query

            response = await self.llm_client.generate_rejected_response(
                user_query=current_query,
                system_prompt=task.system_prompt,
                tools_json=task.to_dict()["tools"],
                conversation_history=conversation_history,
                temperature=0.9
            )
            return response
        except Exception as e:
            self.logger.error(f"生成rejected失败: {str(e)}")
            return None

    async def synthesize_batch(
        self,
        tasks: list[Task],
        enable_step2: bool = False
    ) -> list[Dict]:
        """
        批量合成样本

        Args:
            tasks: 任务列表
            enable_step2: 是否启用Step2

        Returns:
            样本列表
        """
        self.logger.info(f"开始批量合成 {len(tasks)} 个样本")

        # 并发生成
        sample_tasks = [self.synthesize_sample(task, enable_step2) for task in tasks]
        samples = await asyncio.gather(*sample_tasks)

        # 过滤None
        valid_samples = [s for s in samples if s is not None]

        self.logger.info(f"批量合成完成：成功 {len(valid_samples)}/{len(tasks)}")
        return valid_samples

    def __repr__(self) -> str:
        return f"DataSynthesizer(llm_client={self.llm_client})"
