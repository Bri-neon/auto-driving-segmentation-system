from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass(frozen=True)
class Settings:
    app_name: str = "Auto Driving Segmentation Backend"
    app_version: str = "1.0.0"
    api_prefix: str = "/api"
    static_url_prefix: str = "/static"

    default_model_key: str = os.getenv("DEFAULT_MODEL_KEY", "bisenetv2")
    max_upload_size_mb: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "100"))

    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "change-this-in-production")
    jwt_expire_minutes: int = int(os.getenv("JWT_EXPIRE_MINUTES", "120"))
    video_postprocess_mode: str = os.getenv("VIDEO_POSTPROCESS_MODE", "realtime_fast")

    db_host: str = os.getenv("DB_HOST", "127.0.0.1")
    db_port: int = int(os.getenv("DB_PORT", "3306"))
    db_user: str = os.getenv("DB_USER", "root")
    db_password: str = os.getenv("DB_PASSWORD", "123456")
    db_name: str = os.getenv("DB_NAME", "segmentation_system")

    allowed_image_exts: tuple[str, ...] = (".jpg", ".jpeg", ".png")
    allowed_video_exts: tuple[str, ...] = (".mp4", ".avi", ".mov")

    allowed_image_mimes: tuple[str, ...] = ("image/jpeg", "image/png")
    allowed_video_mimes: tuple[str, ...] = (
        "video/mp4",
        "video/x-msvideo",
        "video/quicktime",
    )

    cors_origins: List[str] = None  # type: ignore[assignment]

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


BASE_DIR = Path(__file__).resolve().parents[2]
STATIC_DIR = BASE_DIR / "static"
UPLOAD_DIR = STATIC_DIR / "upload"
RESULT_DIR = STATIC_DIR / "result"
AVATAR_DIR = STATIC_DIR / "avatar"
MODEL_DIR = BASE_DIR / "models"


def get_settings() -> Settings:
    settings = Settings()
    normalized_mode = str(settings.video_postprocess_mode).strip().lower()
    if normalized_mode not in {"realtime_fast", "quality"}:
        normalized_mode = "realtime_fast"
    object.__setattr__(settings, "video_postprocess_mode", normalized_mode)
    object.__setattr__(
        settings,
        "cors_origins",
        ["http://localhost:5173", "http://127.0.0.1:5173"],
    )
    return settings


settings = get_settings()
