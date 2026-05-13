"""Transforme un ordre en langage naturel en plan exécutable."""
import logging

from llm.base import BaseLLM
from orchestrator.tools import TOOLS

log = logging.getLogger(__name__)


class Planner:
    def __init__(self, llm: BaseLLM):
        self.llm = llm

    async def plan(self, user_order: str) -> list[dict]:
        plan = await self.llm.plan(user_order, TOOLS)
        log.info("Plan généré: %s", plan)
        return plan
