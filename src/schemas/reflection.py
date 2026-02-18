from typing import Literal

from pydantic import BaseModel, Field


class Reflection(BaseModel):
    title: str
    summary: str
    themes: list[str] = Field(default_factory=list)
    questions: list[str] = Field(default_factory=list)
    next_thoughts: list[str] = Field(default_factory=list)
    confidence: Literal["high", "medium", "low"]


class EchoRequest(BaseModel):
    transcript: str
