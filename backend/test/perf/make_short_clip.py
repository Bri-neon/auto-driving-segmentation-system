from __future__ import annotations

import argparse
from pathlib import Path

import cv2


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a short clip by taking first N frames.")
    parser.add_argument("--input", default="test/assets/test-1.mp4")
    parser.add_argument("--output", default="test/assets/test-1-short.mp4")
    parser.add_argument("--frames", type=int, default=90)
    args = parser.parse_args()

    src = Path(args.input)
    dst = Path(args.output)
    if not src.exists():
        raise FileNotFoundError(f"input not found: {src}")

    cap = cv2.VideoCapture(str(src))
    if not cap.isOpened():
        raise RuntimeError(f"failed to open input: {src}")

    fps = float(cap.get(cv2.CAP_PROP_FPS))
    if fps <= 0:
        fps = 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    if width <= 0 or height <= 0:
        cap.release()
        raise RuntimeError("invalid source dimensions")

    dst.parent.mkdir(parents=True, exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(dst), fourcc, fps, (width, height))
    if not writer.isOpened():
        cap.release()
        raise RuntimeError(f"failed to create output: {dst}")

    written = 0
    try:
        while written < max(1, args.frames):
            ok, frame = cap.read()
            if not ok:
                break
            writer.write(frame)
            written += 1
    finally:
        cap.release()
        writer.release()

    print("input:", src)
    print("output:", dst)
    print("fps:", fps)
    print("written_frames:", written)
    print("size_mb:", round(dst.stat().st_size / 1024 / 1024, 2))


if __name__ == "__main__":
    main()
