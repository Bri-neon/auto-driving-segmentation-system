import os
from pathlib import Path

cuda_bin_path = r"D:\CUDA\v12.4\bin"
os.environ["PATH"] = cuda_bin_path + ";" + os.environ.get("PATH", "")
if hasattr(os, "add_dll_directory"):
    try:
        os.add_dll_directory(cuda_bin_path)
        print("add_dll_directory ok")
    except Exception as e:
        print("add_dll_directory fail", e)

import onnxruntime as ort

model = Path(r"models\bisenetv2_fp16.onnx")
print("ort version", ort.__version__)
print("available", ort.get_available_providers())

try:
    sess = ort.InferenceSession(str(model), providers=["CUDAExecutionProvider", "CPUExecutionProvider"])
    print("session providers", sess.get_providers())
except Exception as e:
    print("session failed", e)
