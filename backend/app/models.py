from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class SourceState(BaseModel):
    source: str = Field(..., examples=["github"])
    status: str = Field(..., examples=["ok"], description="ok | degraded | down | disabled")
    data: Dict[str, Any] = {}
    error: Optional[str] = None
    fetched_at: Optional[float] = Field(None, description="Unix timestamp of last successful fetch")
    age_seconds: Optional[float] = Field(None, description="Seconds since fetched_at")


class StatsResponse(BaseModel):
    generated_at: float
    healthy: bool = Field(..., description="True if at least one source is ok/degraded")
    sources: Dict[str, SourceState]


class Health(BaseModel):
    status: str = "ok"
    sources: Dict[str, str]
