import ctypes
import os
from pathlib import Path

CAPI_DIR = Path(r".venv\Lib\site-packages\onnxruntime\capi").resolve()
CUDA_BIN = Path(r"D:\CUDA\v12.4\bin")

DLLS = [
    "onnxruntime.dll",
    "onnxruntime_providers_shared.dll",
    "onnxruntime_providers_cuda.dll",
]


def main() -> None:
    print("CAPI_DIR:", CAPI_DIR)
    print("CUDA_BIN:", CUDA_BIN)

    if hasattr(os, "add_dll_directory"):
        if CAPI_DIR.exists():
            os.add_dll_directory(str(CAPI_DIR))
            print("add_dll_directory CAPI OK")
        if CUDA_BIN.exists():
            os.add_dll_directory(str(CUDA_BIN))
            print("add_dll_directory CUDA OK")

    for dll in DLLS:
        p = CAPI_DIR / dll
        if not p.exists():
            print(f"[MISS] {p}")
            continue
        try:
            ctypes.WinDLL(str(p))
            print(f"[OK] {dll}")
        except OSError as ex:
            print(f"[FAIL] {dll}: {ex}")


if __name__ == "__main__":
    main()
