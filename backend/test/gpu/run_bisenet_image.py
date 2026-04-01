import argparse
import os
import time
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort


PALETTE = np.array([
    [128, 64, 128], [244, 35, 232], [70, 70, 70], [102, 102, 156],
    [190, 153, 153], [153, 153, 153], [250, 170, 30], [220, 220, 0],
    [107, 142, 35], [152, 251, 152], [70, 130, 180], [220, 20, 60],
    [255, 0, 0], [0, 0, 142], [0, 0, 70], [0, 60, 100],
    [0, 80, 100], [0, 0, 230], [119, 11, 32]
], dtype=np.uint8)

MEAN = np.array([123.675, 116.28, 103.53], dtype=np.float32)
STD = np.array([58.395, 57.12, 57.375], dtype=np.float32)


def _add_dll_dir(path: str) -> None:
    if not path:
        return
    if not os.path.isdir(path):
        print(f"[WARN] dll dir not found: {path}")
        return

    if path not in os.environ.get("PATH", ""):
        os.environ["PATH"] = path + ";" + os.environ.get("PATH", "")

    if hasattr(os, "add_dll_directory"):
        try:
            os.add_dll_directory(path)
            print(f"[INFO] added dll path: {path}")
        except Exception as ex:
            print(f"[WARN] add_dll_directory failed: {path} | {ex}")


def prepare_runtime_paths(cuda_bin_path: str, extra_dll_dir: str) -> None:
    _add_dll_dir(cuda_bin_path)
    if extra_dll_dir:
        _add_dll_dir(extra_dll_dir)

    capi_dir = Path(ort.__file__).resolve().parent / "capi"
    _add_dll_dir(str(capi_dir))


def create_session(model_path: Path, provider: str) -> ort.InferenceSession:
    sess_options = ort.SessionOptions()
    sess_options.log_severity_level = 3

    if provider == "cpu":
        session = ort.InferenceSession(
            str(model_path), providers=["CPUExecutionProvider"], sess_options=sess_options
        )
        print(f"[INFO] providers: {session.get_providers()}")
        return session

    cuda_provider = (
        "CUDAExecutionProvider",
        {
            "device_id": 0,
            "arena_extend_strategy": "kNextPowerOfTwo",
            "cudnn_conv_algo_search": "EXHAUSTIVE",
            "do_copy_in_default_stream": True,
        },
    )

    if provider == "cuda":
        session = ort.InferenceSession(
            str(model_path), providers=[cuda_provider], sess_options=sess_options
        )
        print(f"[INFO] providers: {session.get_providers()}")
        return session

    try:
        session = ort.InferenceSession(
            str(model_path),
            providers=[cuda_provider, "CPUExecutionProvider"],
            sess_options=sess_options,
        )
        print(f"[INFO] providers: {session.get_providers()}")
        return session
    except Exception as ex:
        print(f"[WARN] CUDA init failed, fallback to CPU: {ex}")
        session = ort.InferenceSession(
            str(model_path), providers=["CPUExecutionProvider"], sess_options=sess_options
        )
        print(f"[INFO] providers: {session.get_providers()}")
        return session


def preprocess(frame_bgr: np.ndarray, input_h: int, input_w: int) -> np.ndarray:
    img = cv2.resize(frame_bgr, (input_w, input_h), interpolation=cv2.INTER_LINEAR)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = (img.astype(np.float32) - MEAN) / STD
    img = img.transpose(2, 0, 1)
    return np.expand_dims(img, axis=0).astype(np.float32)


def decode_output(logits: np.ndarray, input_h: int, input_w: int) -> np.ndarray:
    if logits.ndim == 4:
        mask = np.argmax(logits, axis=1).squeeze().astype(np.uint8)
    elif logits.ndim == 3:
        mask = np.argmax(logits, axis=0).astype(np.uint8)
    else:
        raise ValueError(f"unsupported output shape: {logits.shape}")

    if mask.shape != (input_h, input_w):
        mask = cv2.resize(mask, (input_w, input_h), interpolation=cv2.INTER_NEAREST)

    return mask


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="models/bisenetv2_fp16.onnx")
    parser.add_argument("--image", default="5938.jpg_wh860.jpg")
    parser.add_argument("--outdir", default="test/output")
    parser.add_argument("--input_h", type=int, default=512)
    parser.add_argument("--input_w", type=int, default=1024)
    parser.add_argument("--cuda_bin", default=r"D:\CUDA\v12.4\bin")
    parser.add_argument("--extra_dll_dir", default="")
    parser.add_argument("--provider", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--warmup", type=int, default=1)
    parser.add_argument("--repeat", type=int, default=3)
    args = parser.parse_args()

    model_path = Path(args.model)
    image_path = Path(args.image)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    if not model_path.exists():
        raise FileNotFoundError(f"model not found: {model_path}")
    if not image_path.exists():
        raise FileNotFoundError(f"image not found: {image_path}")

    prepare_runtime_paths(args.cuda_bin, args.extra_dll_dir)
    session = create_session(model_path, args.provider)
    input_name = session.get_inputs()[0].name

    frame = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if frame is None:
        raise RuntimeError(f"failed to read image: {image_path}")

    input_tensor = preprocess(frame, args.input_h, args.input_w)

    for _ in range(max(0, args.warmup)):
        session.run(None, {input_name: input_tensor})

    elapsed_ms = []
    outputs = None
    for _ in range(max(1, args.repeat)):
        t0 = time.time()
        outputs = session.run(None, {input_name: input_tensor})
        elapsed_ms.append((time.time() - t0) * 1000)

    assert outputs is not None
    logits = outputs[0]
    print(f"[INFO] input tensor shape: {input_tensor.shape}")
    print(f"[INFO] output logits shape: {logits.shape}")
    print(f"[INFO] warmup runs: {max(0, args.warmup)}")
    print(f"[INFO] timed runs: {max(1, args.repeat)}")
    print(f"[INFO] avg inference time: {np.mean(elapsed_ms):.2f} ms")
    print(f"[INFO] min inference time: {np.min(elapsed_ms):.2f} ms")

    mask = decode_output(logits, args.input_h, args.input_w)
    color_mask_rgb = PALETTE[np.clip(mask, 0, len(PALETTE) - 1)]
    color_mask_bgr = cv2.cvtColor(color_mask_rgb, cv2.COLOR_RGB2BGR)

    resized = cv2.resize(frame, (args.input_w, args.input_h), interpolation=cv2.INTER_LINEAR)
    overlay = cv2.addWeighted(resized, 0.6, color_mask_bgr, 0.4, 0)

    mask_path = outdir / f"{image_path.stem}_mask.png"
    overlay_path = outdir / f"{image_path.stem}_overlay.png"

    ok1 = cv2.imwrite(str(mask_path), color_mask_bgr)
    ok2 = cv2.imwrite(str(overlay_path), overlay)
    if not (ok1 and ok2):
        raise RuntimeError("failed to save output images")

    unique, counts = np.unique(mask, return_counts=True)
    total = mask.size
    top = sorted(zip(unique.tolist(), counts.tolist()), key=lambda x: x[1], reverse=True)[:5]
    print("[INFO] top classes (id, ratio%):")
    for cid, cnt in top:
        print(f"  - {cid}: {cnt / total * 100:.2f}%")

    print(f"[DONE] mask: {mask_path}")
    print(f"[DONE] overlay: {overlay_path}")


if __name__ == "__main__":
    main()
