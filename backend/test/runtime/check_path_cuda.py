import os
import shutil
from pathlib import Path

CANDIDATE_DIRS = [
    Path(r"D:\CUDA\v12.4\bin"),
    Path(r"D:\CUDA\v12.4\lib\x64"),
    Path(r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4\bin"),
    Path(r"C:\tools\cuda\bin"),
    Path(r"C:\cudnn\bin"),
]

KEY_DLLS = [
    "cudnn64_9.dll",
    "cudnn64_8.dll",
    "cublas64_12.dll",
    "cublasLt64_12.dll",
    "cudart64_12.dll",
    "zlibwapi.dll",
]


def which(exe: str) -> str:
    p = shutil.which(exe)
    return p or "NOT_FOUND"


def main() -> None:
    print("=== BASIC TOOLS ===")
    print("nvidia-smi:", which("nvidia-smi"))
    print("nvcc:", which("nvcc"))

    print("\n=== PATH CHECK ===")
    path_entries = os.environ.get("PATH", "").split(";")
    cuda_related = [p for p in path_entries if "cuda" in p.lower() or "cudnn" in p.lower()]
    if cuda_related:
        for p in cuda_related:
            print("PATH:", p)
    else:
        print("No CUDA/cuDNN related path in current PATH")

    print("\n=== CANDIDATE DIR CHECK ===")
    for d in CANDIDATE_DIRS:
        print(f"{d} -> {'EXISTS' if d.exists() else 'MISSING'}")

    print("\n=== DLL PRESENCE CHECK ===")
    for dll in KEY_DLLS:
        found = []
        for d in CANDIDATE_DIRS:
            p = d / dll
            if p.exists():
                found.append(str(p))
        if found:
            print(f"{dll}: FOUND")
            for p in found:
                print("  ", p)
        else:
            print(f"{dll}: MISSING")


if __name__ == "__main__":
    main()
