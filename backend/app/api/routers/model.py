from __future__ import annotations

from fastapi import APIRouter, Query

from app.core.config import settings
from app.core.responses import success_response
from app.schemas.common import ApiResponse
from app.schemas.model import ModelInfoData
from app.services.model_registry import get_model_config

router = APIRouter(prefix="/model", tags=["model"])


@router.get("/info", response_model=ApiResponse[ModelInfoData])
async def get_model_info(
    model_key: str = Query(default=settings.default_model_key, description="模型标识"),
) -> ApiResponse[ModelInfoData]:
    model = get_model_config(model_key)
    return success_response(
        ModelInfoData(
            model_key=model.model_key,
            model_name=model.model_name,
            framework=model.framework,
            backend=model.backend,
            input_size=[model.input_size[0], model.input_size[1]],
            dataset=model.dataset,
        )
    )
