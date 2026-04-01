from __future__ import annotations

import subprocess
import time
from pathlib import Path

import cv2
import imageio_ffmpeg

from app.core.exceptions import AppException
from app.core.logger import logger

WEB_COMPAT_CODECS = {"h264", "avc1"}


def _normalize_codec(codec: str) -> str:
    # OpenCV fourcc may contain trailing null bytes.
    return codec.replace("\x00", "").strip().lower()


def validate_video_file(path: Path) -> dict[str, float | int | str | bool]:
    if not path.exists():
        raise AppException(f"video validate failed: file not found: {path}")

    size = path.stat().st_size
    if size <= 0:
        raise AppException(f"video validate failed: file empty: {path}")

    cap = cv2.VideoCapture(str(path))
    opened = cap.isOpened()
    fps = float(cap.get(cv2.CAP_PROP_FPS))
    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
    codec_raw = "".join(chr((fourcc >> (8 * i)) & 0xFF) for i in range(4))
    ret, _ = cap.read()
    cap.release()

    if not opened:
        raise AppException(f"video validate failed: cannot open by cv2: {path}")
    if fps <= 0 or frames <= 0:
        raise AppException(f"video validate failed: invalid fps/frames for {path}")
    if width <= 0 or height <= 0:
        raise AppException(f"video validate failed: invalid width/height for {path}")
    if not ret:
        raise AppException(f"video validate failed: cannot read first frame: {path}")

    duration = frames / fps if fps > 0 else 0.0
    if duration <= 0:
        raise AppException(f"video validate failed: invalid duration for {path}")

    return {
        "size": size,
        "fps": round(fps, 3),
        "frames": frames,
        "width": width,
        "height": height,
        "duration": round(duration, 3),
        "codec": _normalize_codec(codec_raw),
    }


def transcode_for_web(input_path: Path, output_path: Path, task_tag: str) -> None:
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [
        ffmpeg_exe,
        "-y",
        "-i",
        str(input_path),
        "-an",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        "-preset",
        "veryfast",
        "-crf",
        "23",
        str(output_path),
    ]

    t0 = time.perf_counter()
    proc = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.perf_counter() - t0

    if proc.returncode != 0:
        stderr_tail = (proc.stderr or "")[-1200:]
        raise AppException(
            f"video transcode failed ({task_tag}): code={proc.returncode}, stderr={stderr_tail}"
        )

    logger.info(
        "video transcode success tag=%s input=%s output=%s elapsed=%.3fs",
        task_tag,
        str(input_path),
        str(output_path),
        elapsed,
    )


def finalize_video_for_web(video_path: Path, task_tag: str) -> dict[str, float | int | str | bool]:
    if not video_path.exists() or video_path.stat().st_size <= 0:
        raise AppException(f"video finalize failed ({task_tag}): source missing or empty")

    temp_path = video_path.with_name(f"{video_path.stem}_webtmp{video_path.suffix}")
    if temp_path.exists():
        temp_path.unlink(missing_ok=True)

    transcode_for_web(video_path, temp_path, task_tag)

    if not temp_path.exists() or temp_path.stat().st_size <= 0:
        raise AppException(f"video finalize failed ({task_tag}): transcoded file missing")

    if video_path.exists():
        video_path.unlink(missing_ok=True)
    temp_path.replace(video_path)

    meta = validate_video_file(video_path)
    codec = str(meta.get("codec", "")).lower()
    if codec not in WEB_COMPAT_CODECS:
        raise AppException(
            f"video finalize failed ({task_tag}): incompatible codec={codec}, expected h264/avc1"
        )

    logger.info(
        "video validate success tag=%s path=%s codec=%s duration=%s size=%s",
        task_tag,
        str(video_path),
        meta.get("codec"),
        meta.get("duration"),
        meta.get("size"),
    )
    return meta
