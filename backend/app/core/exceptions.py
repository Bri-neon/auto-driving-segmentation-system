from __future__ import annotations

import traceback
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logger import logger
from app.core.responses import error_response


class AppException(Exception):
    def __init__(self, message: str, status_code: int = HTTPStatus.BAD_REQUEST, code: int = 1001) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = int(status_code)
        self.code = code


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def handle_app_exception(request: Request, exc: AppException) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "-")
        logger.warning(
            "request_id=%s method=%s path=%s status=%s error=%s",
            request_id,
            request.method,
            request.url.path,
            exc.status_code,
            exc.message,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(message=exc.message, code=exc.code).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_exception(request: Request, exc: RequestValidationError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "-")
        message = "请求参数校验失败"
        logger.warning(
            "request_id=%s method=%s path=%s status=%s error=%s detail=%s",
            request_id,
            request.method,
            request.url.path,
            HTTPStatus.UNPROCESSABLE_ENTITY,
            message,
            exc.errors(),
        )
        return JSONResponse(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            content=error_response(message=message).model_dump(),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "-")
        message = str(exc.detail) if exc.detail else "请求处理失败"
        logger.warning(
            "request_id=%s method=%s path=%s status=%s error=%s",
            request_id,
            request.method,
            request.url.path,
            exc.status_code,
            message,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(message=message).model_dump(),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "-")
        logger.error(
            "request_id=%s method=%s path=%s status=%s error=%s traceback=%s",
            request_id,
            request.method,
            request.url.path,
            HTTPStatus.INTERNAL_SERVER_ERROR,
            str(exc),
            traceback.format_exc(),
        )
        return JSONResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            content=error_response(message="服务器内部错误").model_dump(),
        )
