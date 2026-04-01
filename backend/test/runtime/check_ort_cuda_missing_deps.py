import ctypes
import os
from pathlib import Path

import pefile

CAPI_DIR = Path(r".venv\Lib\site-packages\onnxruntime\capi").resolve()
CAPI_DLL = CAPI_DIR / "onnxruntime_providers_cuda.dll"
CUDA_BIN = Path(r"D:\CUDA\v12.4\bin")


def main() -> None:
    if not CAPI_DLL.exists():
        print("[FAIL] not found:", CAPI_DLL)
        return

    if hasattr(os, "add_dll_directory"):
        if CUDA_BIN.exists():
            os.add_dll_directory(str(CUDA_BIN))
        if CAPI_DIR.exists():
            os.add_dll_directory(str(CAPI_DIR))

    if CUDA_BIN.exists():
        os.environ["PATH"] = str(CUDA_BIN) + ";" + os.environ.get("PATH", "")
    os.environ["PATH"] = str(CAPI_DIR) + ";" + os.environ.get("PATH", "")

    pe = pefile.PE(str(CAPI_DLL))
    imports = []
    if hasattr(pe, "DIRECTORY_ENTRY_IMPORT"):
        imports = [e.dll.decode(errors="ignore") for e in pe.DIRECTORY_ENTRY_IMPORT]

    print("[INFO] provider dll:", CAPI_DLL)
    print("[INFO] imported dll count:", len(imports))

    failed = []
    for dll in imports:
        try:
            ctypes.WinDLL(dll)
            print("[OK]", dll)
        except OSError as ex:
            print("[MISS]", dll, "=>", ex)
            failed.append(dll)

    print("\n=== SUMMARY ===")
    if failed:
        print("missing deps:")
        for d in failed:
            print(" -", d)
    else:
        print("all imported deps loadable")


if __name__ == "__main__":
    main()
