"""Interface abstraite pour les clients LLM."""
from abc import ABC, abstractmethod


class BaseLLM(ABC):
    @abstractmethod
    async def plan(self, user_order: str, tools: list[dict]) -> list[dict]:
        """Transforme un ordre en langage naturel en liste d'appels d'outils."""
        raise NotImplementedError
