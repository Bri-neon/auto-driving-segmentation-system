from __future__ import annotations

import re
import time
import uuid
from http import HTTPStatus
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import AppException

_PREFIX_PATTERN = re.compile(r"[^a-zA-Z0-9_-]+")


def ensure_dirs(*paths: Path) -> None:
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)


def build_unique_filename(original_name: str, prefix: str | None = None) -> str:
    suffix = Path(original_name).suffix.lower()
    base = f"{uuid.uuid4().hex}_{int(time.time() * 1000)}{suffix}"
    if not prefix:
        return base
    safe_prefix = _PREFIX_PATTERN.sub("_", prefix).strip("_")
    if not safe_prefix:
        return base
    return f"{safe_prefix}_{base}"


def validate_upload_file(file: UploadFile, file_type: str) -> None:
    ext = Path(file.filename or "").suffix.lower()
    content_type = (file.content_type or "").lower()

    if file_type == "image":
        allowed_exts = settings.allowed_image_exts
        allowed_mimes = settings.allowed_image_mimes
    elif file_type == "video":
        allowed_exts = settings.allowed_video_exts
        allowed_mimes = settings.allowed_video_mimes
    else:
        raise AppException("未知文件类型", status_code=HTTPStatus.BAD_REQUEST)

    if ext not in allowed_exts:
        raise AppException(
            message=f"文件扩展名不支持: {ext}",
            status_code=HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
        )

    if content_type not in allowed_mimes:
        raise AppException(
            message=f"文件 MIME 类型不支持: {content_type or 'unknown'}",
            status_code=HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
        )


async def save_upload_file(file: UploadFile, destination: Path) -> int:
    total_size = 0
    chunk_size = 1024 * 1024

    with destination.open("wb") as out:
        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            total_size += len(chunk)
            if total_size > settings.max_upload_size_bytes:
                raise AppException(
                    message=f"文件过大，最大支持 {settings.max_upload_size_mb}MB",
                    status_code=HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                )
            out.write(chunk)

    await file.close()
    return total_size
