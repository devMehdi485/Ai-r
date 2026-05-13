"""Client Groq utilisant Llama 3.3 70B."""
import json

from groq import AsyncGroq

import config
from llm.base import BaseLLM
from llm.prompts import PLANNER_SYSTEM


class GroqClient(BaseLLM):
    def __init__(self):
        if not config.GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY manquante dans .env")
        self.client = AsyncGroq(api_key=config.GROQ_API_KEY)
        self.model = config.LLM_MODEL_GROQ

    async def plan(self, user_order: str, tools: list[dict]) -> list[dict]:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": PLANNER_SYSTEM},
                {"role": "user", "content": user_order},
            ],
            tools=tools,
            tool_choice="auto",
            temperature=config.LLM_TEMPERATURE,
        )
        message = response.choices[0].message
        if not message.tool_calls:
            return []
        return [
            {
                "name": tc.function.name,
                "arguments": json.loads(tc.function.arguments) if tc.function.arguments else {},
            }
            for tc in message.tool_calls
        ]
