import os
from pathlib import Path

import onnxruntime as ort

MODEL = Path(r"models\bisenetv2_fp16.onnx").resolve()
CUDA_BIN = Path(r"D:\CUDA\v12.4\bin").resolve()


def main() -> None:
    keep = []
    for p in os.environ.get("PATH", "").split(";"):
        pl = p.lower()
        if "cuda\\v13.1" in pl:
            continue
        keep.append(p)
    os.environ["PATH"] = ";".join(keep)

    if CUDA_BIN.exists() and str(CUDA_BIN) not in os.environ["PATH"]:
        os.environ["PATH"] = str(CUDA_BIN) + ";" + os.environ["PATH"]

    if hasattr(os, "add_dll_directory"):
        os.add_dll_directory(str(CUDA_BIN))

    print("ORT:", ort.__version__)
    print("PATH contains v13.1:", any("cuda\\v13.1" in p.lower() for p in os.environ["PATH"].split(";")))

    try:
        s = ort.InferenceSession(str(MODEL), providers=["CUDAExecutionProvider", "CPUExecutionProvider"])
        print("session providers:", s.get_providers())
    except Exception as ex:
        print("session failed:", ex)


if __name__ == "__main__":
    main()
