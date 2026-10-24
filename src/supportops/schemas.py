from typing import Literal

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    query: str = Field(min_length=3, max_length=1000, description="Question about the indexed IT docs")


class SourceItem(BaseModel):
    source: str
    chunk_id: str
    excerpt: str
    distance: float


class AskResponse(BaseModel):
    request_id: str
    answer: str
    sources: list[SourceItem]
    latency_ms: float


class FeedbackRequest(BaseModel):
    request_id: str = Field(min_length=1, max_length=100)
    rating: Literal[1, 2, 3, 4, 5]
    comment: str | None = Field(default=None, max_length=2000)


class FeedbackResponse(BaseModel):
    status: str
    feedback_id: int
