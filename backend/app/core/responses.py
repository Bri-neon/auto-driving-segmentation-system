from __future__ import annotations

from typing import Any

from app.schemas.common import ApiResponse


def success_response(data: Any) -> ApiResponse[Any]:
    return ApiResponse[Any](code=0, message="success", data=data)


def error_response(message: str, code: int = 1001) -> ApiResponse[None]:
    return ApiResponse[None](code=code, message=message, data=None)
