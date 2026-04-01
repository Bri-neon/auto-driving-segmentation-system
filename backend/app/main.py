from __future__ import annotations

import time
import uuid
from http import HTTPStatus

import imageio_ffmpeg
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.staticfiles import StaticFiles

from app.api.routers.auth import router as auth_router
from app.api.routers.admin import router as admin_router
from app.api.routers.health import router as health_router
from app.api.routers.history import router as history_router
from app.api.routers.model import router as model_router
from app.api.routers.segment import router as segment_router
from app.core.config import AVATAR_DIR, RESULT_DIR, STATIC_DIR, UPLOAD_DIR, settings
from app.core.exceptions import register_exception_handlers
from app.core.logger import logger
from app.core.responses import error_response
from app.utils.file_utils import ensure_dirs

app = FastAPI(
    title="Auto Driving Segmentation API",
    version=settings.app_version,
    description="自动驾驶图像语义分割系统后端接口",
)

ensure_dirs(STATIC_DIR, UPLOAD_DIR, RESULT_DIR, AVATAR_DIR)
logger.info("video finalize ready ffmpeg_exe=%s", imageio_ffmpeg.get_ffmpeg_exe())

app.mount(settings.static_url_prefix, StaticFiles(directory=STATIC_DIR), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", uuid.uuid4().hex)
    request.state.request_id = request_id

    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit():
        if int(content_length) > settings.max_upload_size_bytes:
            logger.warning(
                "request_id=%s method=%s path=%s status=%s error=%s",
                request_id,
                request.method,
                request.url.path,
                HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                "payload too large by content-length",
            )
            return JSONResponse(
                status_code=HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                content=error_response(
                    message=f"文件过大，最大支持 {settings.max_upload_size_mb}MB"
                ).model_dump(),
            )

    start = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - start

    response.headers["X-Request-ID"] = request_id
    logger.info(
        "request_id=%s method=%s path=%s status=%s elapsed=%.3fs",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        elapsed,
    )
    return response


app.include_router(health_router, prefix=settings.api_prefix)
app.include_router(model_router, prefix=settings.api_prefix)
app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(admin_router, prefix=settings.api_prefix)
app.include_router(history_router, prefix=settings.api_prefix)
app.include_router(segment_router, prefix=settings.api_prefix)

register_exception_handlers(app)
