from pathlib import Path
import pefile

DLL = Path(r".venv\Lib\site-packages\onnxruntime\capi\onnxruntime_providers_cuda.dll")


def main() -> None:
    if not DLL.exists():
        print("missing", DLL)
        return
    pe = pefile.PE(str(DLL))
    deps = []
    if hasattr(pe, "DIRECTORY_ENTRY_IMPORT"):
        for entry in pe.DIRECTORY_ENTRY_IMPORT:
            deps.append(entry.dll.decode(errors="ignore"))

    print("Imported DLL count:", len(deps))
    for d in deps:
        print(d)


if __name__ == "__main__":
    main()
