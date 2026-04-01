from __future__ import annotations

from fastapi import APIRouter

from app.core.responses import success_response
from app.schemas.common import ApiResponse, HealthData

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=ApiResponse[HealthData])
async def health_check() -> ApiResponse[HealthData]:
    return success_response(HealthData(status="ok"))
