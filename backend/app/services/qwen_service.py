"""通义千问 API 服务封装"""
import json
import httpx
from typing import Optional
from app.core.config import get_settings

settings = get_settings()


class QwenService:
    """通义千问 API 服务"""
    
    def __init__(self):
        self.api_key = settings.qwen_api_key
        self.model = settings.qwen_model
        self.base_url = settings.qwen_base_url
        
    async def _chat(self, messages: list[dict], temperature: float = 0.7) -> str:
        """调用通义千问聊天接口"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                },
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
    
    async def extract_key_points(self, content: str, direction: str) -> list[dict]:
        """从资料中提炼核心知识点"""
        prompt = f"""你是一位专业的{direction}领域教师。请从以下学习资料中提炼5-10个核心知识点。

学习资料：
{content}

请以JSON数组格式返回，每个知识点包含：
- point: 知识点名称
- description: 简要描述
- importance: 重要程度(1-5)

只返回JSON数组，不要其他内容。"""

        messages = [{"role": "user", "content": prompt}]
        result = await self._chat(messages, temperature=0.3)
        
        # 解析JSON
        try:
            # 尝试提取JSON部分
            result = result.strip()
            if result.startswith("```"):
                result = result.split("```")[1]
                if result.startswith("json"):
                    result = result[4:]
            return json.loads(result)
        except json.JSONDecodeError:
            return [{"point": "知识点提取失败", "description": result, "importance": 3}]
    
    async def generate_questions(
        self, 
        key_points: list[dict], 
        direction: str,
        question_types: Optional[list[str]] = None
    ) -> list[dict]:
        """基于知识点生成题目"""
        if question_types is None:
            question_types = ["single_choice", "multi_choice", "true_false", "short_answer"]
        
        points_text = "\n".join([f"- {p['point']}: {p['description']}" for p in key_points])
        types_text = ", ".join(question_types)
        
        prompt = f"""你是一位专业的{direction}领域出题教师。请基于以下知识点生成测试题目。

知识点：
{points_text}

要求：
1. 为每个知识点生成1-2道题目
2. 题型包括：{types_text}
3. 难度分布均匀(1-5)
4. 选择题需要4个选项

请以JSON数组格式返回，每道题包含：
- type: 题型(single_choice/multi_choice/true_false/short_answer)
- difficulty: 难度(1-5)
- content: 题目内容
- options: 选项数组(选择题必填，判断题为["正确","错误"])
- answer: 标准答案(选择题为正确选项，判断题为"正确"或"错误"，简答题为答案要点)
- explanation: 答案解析
- knowledge_point: 对应的知识点

只返回JSON数组，不要其他内容。"""

        messages = [{"role": "user", "content": prompt}]
        result = await self._chat(messages, temperature=0.5)
        
        # 解析JSON
        try:
            result = result.strip()
            if result.startswith("```"):
                result = result.split("```")[1]
                if result.startswith("json"):
                    result = result[4:]
            return json.loads(result)
        except json.JSONDecodeError:
            return []
    
    async def evaluate_answer(
        self,
        question: str,
        standard_answer: str,
        user_answer: str,
        question_type: str
    ) -> dict:
        """评估主观题答案"""
        prompt = f"""你是一位专业的阅卷教师。请评估学生的答案。

题目：{question}

标准答案要点：{standard_answer}

学生答案：{user_answer}

请以JSON格式返回评分结果：
- score: 得分(0-100)
- feedback: 评语(指出答案的优点和不足)
- key_points_hit: 命中的要点
- key_points_missed: 遗漏的要点

只返回JSON对象，不要其他内容。"""

        messages = [{"role": "user", "content": prompt}]
        result = await self._chat(messages, temperature=0.3)
        
        # 解析JSON
        try:
            result = result.strip()
            if result.startswith("```"):
                result = result.split("```")[1]
                if result.startswith("json"):
                    result = result[4:]
            return json.loads(result)
        except json.JSONDecodeError:
            return {"score": 0, "feedback": "评分失败，请重试"}


# 单例
qwen_service = QwenService()
