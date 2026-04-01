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
MODEL_DIR = BASE_DIR / "models"


def get_settings() -> Settings:
    settings = Settings()
    object.__setattr__(
        settings,
        "cors_origins",
        ["http://localhost:5173", "http://127.0.0.1:5173"],
    )
    return settings


settings = get_settings()
