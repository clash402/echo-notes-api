from typing import Literal

from backend.src.core.settings import get_settings


class ModelRouter:
    def route(self, *, tier: Literal["cheap", "default"] = "default") -> str:
        settings = get_settings()
        return settings.llm_cheap_model if tier == "cheap" else settings.llm_default_model
