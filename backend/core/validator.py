"""
验证器模块
负责校验和修正生成的DPO样本
"""

import re
import json
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING
from .utils import setup_logger, validate_json_structure

if TYPE_CHECKING:
    from services.llm_client import LLMClient


class Validator:
    """样本验证器"""

    def __init__(self, strict_mode: bool = False, llm_client: Optional['LLMClient'] = None):
        """
        初始化验证器

        Args:
            strict_mode: 严格模式（更严格的验证规则）
            llm_client: LLM客户端，用于模型自评验证
        """
        self.strict_mode = strict_mode
        self.llm_client = llm_client
        self.logger = setup_logger("Validator")

    def validate_sample(self, sample: Dict) -> Tuple[bool, List[str]]:
        """
        验证样本是否合法

        Args:
            sample: DPO样本

        Returns:
            (是否合法, 错误列表)
        """
        errors = []

        # 1. 验证必需字段
        required_fields = ["system", "tools", "messages", "chosen", "rejected"]
        if not validate_json_structure(sample, required_fields):
            missing = [f for f in required_fields if f not in sample]
            errors.append(f"缺少必需字段: {missing}")
            return False, errors

        # 2. 验证tools格式
        try:
            tools = json.loads(sample["tools"]) if isinstance(sample["tools"], str) else sample["tools"]
            if not isinstance(tools, list) or len(tools) == 0:
                errors.append("tools必须是非空列表")
        except json.JSONDecodeError:
            errors.append("tools不是有效的JSON")

        # 3. 验证messages格式
        messages = sample.get("messages", [])
        if not isinstance(messages, list) or len(messages) == 0:
            errors.append("messages必须是非空列表")
        else:
            for msg in messages:
                if "role" not in msg or "content" not in msg:
                    errors.append("messages中的消息缺少role或content字段")

        # 4. 验证chosen和rejected格式
        chosen = sample.get("chosen", "")
        rejected = sample.get("rejected", "")

        if not chosen or not rejected:
            errors.append("chosen或rejected为空")

        # 5. 检查function_call标签（宽松模式：允许各种合理的回复形式）
        chosen_has_call = self._has_function_call_tag(chosen)
        rejected_has_call = self._has_function_call_tag(rejected)

        # 新规则：chosen和rejected都可以不包含function_call
        # 常见情况：
        # - chosen: function_call (正确调用) vs rejected: 没有调用工具（错误地直接回答）
        # - chosen: function_call vs rejected: function_call（错误的工具或参数）
        # - chosen: 澄清问题 vs rejected: function_call（错误地直接调用）
        # - chosen: 澄清问题 vs rejected: 直接回答（都没调用，但chosen更合理）

        # 6. 验证function_call内容（只验证存在的function_call，且只做基本检查）
        if chosen_has_call:
            chosen_valid, chosen_err = self._validate_function_call(chosen, tools if 'tools' in locals() else [])
            # 只记录警告，不作为错误
            if not chosen_valid:
                self.logger.debug(f"chosen的function_call格式问题: {chosen_err}")

        if rejected_has_call:
            rejected_valid, rejected_err = self._validate_function_call(rejected, tools if 'tools' in locals() else [])
            # rejected可以有格式错误（这本身就是一种错误类型）
            if not rejected_valid:
                self.logger.debug(f"rejected的function_call格式问题（可能是故意的错误）: {rejected_err}")

        # 7. 检查chosen和rejected的差异
        if chosen == rejected:
            errors.append("chosen和rejected完全相同")

        is_valid = len(errors) == 0
        return is_valid, errors

    def _has_function_call_tag(self, text: str) -> bool:
        """检查是否包含function_call标签"""
        return "<function_call>" in text and "</function_call>" in text

    def _validate_function_call(self, text: str, tools: List[Dict]) -> Tuple[bool, str]:
        """
        验证function_call内容

        Args:
            text: 包含function_call的文本
            tools: 可用工具列表

        Returns:
            (是否有效, 错误信息)
        """
        try:
            # 提取function_call内容
            match = re.search(r'<function_call>\s*(.*?)\s*</function_call>', text, re.DOTALL)
            if not match:
                return False, "未找到function_call标签"

            func_call_text = match.group(1).strip()

            # 解析JSON
            try:
                func_call = json.loads(func_call_text)
            except json.JSONDecodeError:
                return False, "function_call内容不是有效的JSON"

            # 验证必需字段
            if "name" not in func_call:
                return False, "缺少name字段"

            if "arguments" not in func_call:
                return False, "缺少arguments字段"

            # 验证工具名是否存在
            tool_name = func_call["name"]
            tool_names = [t.get("name", "") for t in tools]

            if tool_name not in tool_names:
                return False, f"工具 {tool_name} 不在可用工具列表中"

            # 验证arguments是字典
            if not isinstance(func_call["arguments"], dict):
                return False, "arguments必须是对象类型"

            return True, ""

        except Exception as e:
            return False, f"验证异常: {str(e)}"

    async def validate_with_llm(self, sample: Dict) -> Tuple[bool, List[str], Optional[Dict]]:
        """
        使用LLM进行深度验证（模型自评）

        Args:
            sample: 样本数据

        Returns:
            (是否有效, 错误列表, LLM评估结果)
        """
        if not self.llm_client:
            self.logger.warning("未设置LLM客户端，跳过模型自评")
            return True, [], None

        try:
            # 调用LLM进行验证
            llm_result = await self.llm_client.validate_and_correct(sample)

            is_valid = llm_result.get("is_valid", True)
            issues = llm_result.get("issues", [])
            quality_score = llm_result.get("quality_score", 7.0)
            similarity_score = llm_result.get("similarity_score", 50.0)

            # 根据评分决定是否有效
            errors = []

            if quality_score < 5.0:
                errors.append(f"Chosen质量评分过低: {quality_score}/10")

            if similarity_score > 80.0:
                errors.append(f"Chosen和Rejected相似度过高: {similarity_score}%")

            if issues:
                errors.extend(issues)

            is_valid = len(errors) == 0 and is_valid

            return is_valid, errors, llm_result

        except Exception as e:
            self.logger.error(f"LLM验证失败: {str(e)}")
            return True, [], None

    def validate_batch(self, samples: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        批量验证样本（格式验证）

        Args:
            samples: 样本列表

        Returns:
            (合法样本列表, 非法样本列表)
        """
        valid_samples = []
        invalid_samples = []

        for sample in samples:
            is_valid, errors = self.validate_sample(sample)

            if is_valid:
                valid_samples.append(sample)
            else:
                sample["validation_errors"] = errors
                invalid_samples.append(sample)
                self.logger.warning(f"样本验证失败: {sample.get('task_id', 'unknown')}, 错误: {errors}")

        self.logger.info(f"批量验证完成：合法 {len(valid_samples)}/{len(samples)}")
        return valid_samples, invalid_samples

    async def validate_batch_with_llm(self, samples: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        批量验证样本（格式验证 + LLM自评）

        Args:
            samples: 样本列表

        Returns:
            (合法样本列表, 非法样本列表)
        """
        valid_samples = []
        invalid_samples = []

        for sample in samples:
            # 第一步：格式验证（快速）
            is_format_valid, format_errors = self.validate_sample(sample)

            if not is_format_valid:
                sample["validation_errors"] = format_errors
                sample["validation_type"] = "format"
                invalid_samples.append(sample)
                self.logger.warning(f"样本格式验证失败: {sample.get('task_id', 'unknown')}")
                continue

            # 第二步：LLM验证（准确）
            is_llm_valid, llm_errors, llm_result = await self.validate_with_llm(sample)

            if is_llm_valid:
                # 添加质量评分到样本
                if llm_result:
                    sample["quality_score"] = llm_result.get("quality_score", 7.0)
                    sample["similarity_score"] = llm_result.get("similarity_score", 50.0)
                valid_samples.append(sample)
            else:
                sample["validation_errors"] = llm_errors
                sample["validation_type"] = "llm"
                invalid_samples.append(sample)
                self.logger.warning(f"样本LLM验证失败: {sample.get('task_id', 'unknown')}, 原因: {llm_errors}")

        self.logger.info(f"批量验证完成（含LLM自评）：合法 {len(valid_samples)}/{len(samples)}")
        return valid_samples, invalid_samples

    def auto_correct(self, sample: Dict) -> Optional[Dict]:
        """
        尝试自动修正样本

        Args:
            sample: 待修正的样本

        Returns:
            修正后的样本，如果无法修正则返回None
        """
        # 基础修正策略
        corrected = sample.copy()

        # 1. 修正tools格式
        if isinstance(corrected.get("tools"), list):
            corrected["tools"] = json.dumps(corrected["tools"], ensure_ascii=False)

        # 2. 修正空字段
        if not corrected.get("chosen"):
            return None  # 无法修正

        if not corrected.get("rejected"):
            return None  # 无法修正

        # 3. 移除多余空白
        corrected["chosen"] = corrected["chosen"].strip()
        corrected["rejected"] = corrected["rejected"].strip()

        # 验证修正后的样本
        is_valid, errors = self.validate_sample(corrected)

        if is_valid:
            self.logger.info(f"样本修正成功: {sample.get('task_id', 'unknown')}")
            return corrected
        else:
            self.logger.warning(f"样本修正失败: {errors}")
            return None

    def get_validation_statistics(self, samples: List[Dict]) -> Dict:
        """
        获取验证统计信息

        Args:
            samples: 样本列表

        Returns:
            统计信息字典
        """
        valid_count = 0
        invalid_count = 0
        error_types = {}

        for sample in samples:
            is_valid, errors = self.validate_sample(sample)

            if is_valid:
                valid_count += 1
            else:
                invalid_count += 1
                for error in errors:
                    error_types[error] = error_types.get(error, 0) + 1

        return {
            "total": len(samples),
            "valid": valid_count,
            "invalid": invalid_count,
            "success_rate": valid_count / len(samples) if samples else 0,
            "error_types": error_types
        }

    def __repr__(self) -> str:
        return f"Validator(strict_mode={self.strict_mode})"
