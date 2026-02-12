"""知识提取 AI 服务 - 基于通义千问提取知识点和最佳实践"""
import json
import logging
import httpx
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class KnowledgeService:
    """知识提取 AI 服务"""

    def __init__(self):
        self.api_key = settings.qwen_api_key
        self.model = settings.qwen_model
        self.base_url = settings.qwen_base_url

    async def _chat(self, messages: list[dict], temperature: float = 0.7) -> str:
        """调用通义千问聊天接口"""
        async with httpx.AsyncClient(timeout=120.0) as client:
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

    def _parse_json(self, text: str) -> dict | list | None:
        """解析大模型返回的 JSON，带容错处理"""
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            logger.error("JSON 解析失败，原始内容: %s", text[:500])
            return None

    async def extract_knowledge_and_practices(self, raw_text: str) -> dict:
        """从内容中提炼知识点、最佳实践和摘要"""
        prompt = f"""你是一位专业的知识管理专家。请对以下内容进行深度分析，提炼核心知识点并总结最佳实践。

【内容】：
{raw_text}

【任务要求】：
1. 提炼 5-10 个核心知识点，每个知识点包含：
   - name: 知识点名称（简洁明了）
   - description: 详细描述（100-200字）
   - importance: 重要程度（1-5，5最重要）
   - category: 分类标签（如"技术原理"、"工具使用"、"设计模式"、"方法论"等）

2. 总结 3-8 条最佳实践建议，每条包含：
   - title: 实践标题（简洁明了）
   - content: 具体内容（详细描述该实践的做法）
   - scenario: 适用场景（在什么情况下应该使用）
   - notes: 注意事项（需要避免的坑或特别提醒）

3. 生成一段内容摘要（100-200字，概括核心要点）

【输出格式】：
请严格以JSON格式返回，结构如下：
{{
  "summary": "内容摘要...",
  "knowledge_points": [
    {{
      "name": "...",
      "description": "...",
      "importance": 5,
      "category": "..."
    }}
  ],
  "best_practices": [
    {{
      "title": "...",
      "content": "...",
      "scenario": "...",
      "notes": "..."
    }}
  ]
}}

只返回JSON，不要其他内容。"""

        messages = [{"role": "user", "content": prompt}]
        result = await self._chat(messages, temperature=0.3)

        parsed = self._parse_json(result)
        if parsed and isinstance(parsed, dict):
            return parsed

        # 解析失败时返回默认结构
        return {
            "summary": "内容解析失败，请重试。",
            "knowledge_points": [],
            "best_practices": [],
        }


# 单例
knowledge_service = KnowledgeService()
