from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from pathlib import Path

from app.core.config import MODEL_DIR
from app.core.exceptions import AppException


@dataclass(frozen=True)
class ModelConfig:
    model_key: str
    model_name: str
    input_size: tuple[int, int]  # (H, W)
    model_filename: str
    framework: str = "ONNX Runtime"
    backend: str = "FastAPI"
    dataset: str = "Cityscapes"

    @property
    def model_path(self) -> Path:
        return MODEL_DIR / self.model_filename


MODEL_REGISTRY: dict[str, ModelConfig] = {
    "deeplabv3plus_resnet50": ModelConfig(
        model_key="deeplabv3plus_resnet50",
        model_name="DeepLabV3+ ResNet50 FP16",
        input_size=(512, 512),
        model_filename="deeplabv3plus_resnet50_fp16.onnx",
    ),
    "bisenetv2": ModelConfig(
        model_key="bisenetv2",
        model_name="BiSeNetV2 FP16",
        input_size=(512, 1024),
        model_filename="bisenetv2_fp16.onnx",
    ),
}


def get_model_config(model_key: str) -> ModelConfig:
    if model_key not in MODEL_REGISTRY:
        raise AppException(
            message=f"不支持的 model_key: {model_key}",
            status_code=HTTPStatus.BAD_REQUEST,
        )
    return MODEL_REGISTRY[model_key]


def list_model_keys() -> list[str]:
    return list(MODEL_REGISTRY.keys())
