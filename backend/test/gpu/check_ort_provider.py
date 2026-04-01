import os
from pathlib import Path

import onnxruntime as ort

MODEL = Path(r"models\bisenetv2_fp16.onnx")


def main() -> None:
    print("onnxruntime version:", ort.__version__)
    print("available providers:", ort.get_available_providers())

    cuda_bin = os.getenv("CUDA_BIN_PATH", r"D:\CUDA\v12.4\bin")
    if Path(cuda_bin).exists() and hasattr(os, "add_dll_directory"):
        try:
            os.add_dll_directory(cuda_bin)
            print("add_dll_directory:", cuda_bin)
        except OSError as ex:
            print("add_dll_directory failed:", ex)

    if not MODEL.exists():
        print("model missing:", MODEL)
        return

    print("\n--- try CUDA only ---")
    try:
        s = ort.InferenceSession(str(MODEL), providers=["CUDAExecutionProvider"])
        print("CUDA only session providers:", s.get_providers())
    except Exception as ex:
        print("CUDA only failed:", ex)

    print("\n--- try CUDA + CPU ---")
    try:
        s = ort.InferenceSession(str(MODEL), providers=["CUDAExecutionProvider", "CPUExecutionProvider"])
        print("CUDA+CPU session providers:", s.get_providers())
    except Exception as ex:
        print("CUDA+CPU failed:", ex)

    print("\n--- try CPU only ---")
    try:
        s = ort.InferenceSession(str(MODEL), providers=["CPUExecutionProvider"])
        print("CPU only session providers:", s.get_providers())
    except Exception as ex:
        print("CPU only failed:", ex)


if __name__ == "__main__":
    main()
