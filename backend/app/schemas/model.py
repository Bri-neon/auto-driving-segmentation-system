from __future__ import annotations

from pydantic import BaseModel, Field


class ModelInfoData(BaseModel):
    model_key: str = Field(..., description="model unique key")
    model_name: str
    framework: str
    backend: str
    input_size: list[int]
    dataset: str
