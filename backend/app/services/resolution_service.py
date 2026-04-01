from __future__ import annotations

from http import HTTPStatus

from app.core.exceptions import AppException
from app.schemas.segment import SegmentResolutionOption

RESOLUTION_PRESETS: dict[str, tuple[int, int]] = {
    "512x1024": (512, 1024),
    "384x768": (384, 768),
    "320x640": (320, 640),
    "256x512": (256, 512),
}

DEFAULT_RESOLUTION_KEY = "512x1024"


def list_resolution_options() -> list[SegmentResolutionOption]:
    return [
        SegmentResolutionOption(
            key=key,
            input_size=[value[0], value[1]],
            label=f"{value[0]}x{value[1]}",
        )
        for key, value in RESOLUTION_PRESETS.items()
    ]


def parse_resolution_or_default(resolution: str | None, fallback: tuple[int, int]) -> tuple[int, int]:
    if not resolution:
        return fallback

    normalized = resolution.strip().lower()
    if normalized in RESOLUTION_PRESETS:
        return RESOLUTION_PRESETS[normalized]

    available = ", ".join(RESOLUTION_PRESETS.keys())
    raise AppException(
        message=f"不支持的 resolution: {resolution}，可选: {available}",
        status_code=HTTPStatus.BAD_REQUEST,
    )
