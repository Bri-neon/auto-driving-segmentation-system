import ctypes
import os
from pathlib import Path

ORT_CUDA_DLL = Path(r".venv\Lib\site-packages\onnxruntime\capi\onnxruntime_providers_cuda.dll")
CANDIDATE_DLLS = [
    "cudnn64_9.dll",
    "cudnn64_8.dll",
    "cublas64_12.dll",
    "cublasLt64_12.dll",
    "cudart64_12.dll",
    "zlibwapi.dll",
]


def try_load(dll_name: str) -> None:
    try:
        ctypes.WinDLL(dll_name)
        print(f"[OK] load {dll_name}")
    except OSError as ex:
        print(f"[FAIL] load {dll_name}: {ex}")


def main() -> None:
    cuda_bin = os.getenv("CUDA_BIN_PATH", r"D:\CUDA\v12.4\bin")
    if Path(cuda_bin).exists() and hasattr(os, "add_dll_directory"):
        try:
            os.add_dll_directory(cuda_bin)
            print("[INFO] add_dll_directory:", cuda_bin)
        except OSError as ex:
            print("[WARN] add_dll_directory failed:", ex)

    print("\n=== DEP DLLS ===")
    for dll in CANDIDATE_DLLS:
        try_load(dll)

    print("\n=== ORT CUDA PROVIDER DLL ===")
    if not ORT_CUDA_DLL.exists():
        print("[FAIL] not found:", ORT_CUDA_DLL)
        return

    try:
        ctypes.WinDLL(str(ORT_CUDA_DLL))
        print("[OK] load onnxruntime_providers_cuda.dll")
    except OSError as ex:
        print("[FAIL] load onnxruntime_providers_cuda.dll:", ex)


if __name__ == "__main__":
    main()
