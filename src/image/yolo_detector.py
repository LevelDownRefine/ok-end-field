from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from ok import Box


@dataclass(slots=True)
class YoloDetection:
    """单个 YOLO 检测结果。"""

    cls_id: int
    cls_name: str
    confidence: float
    x1: int
    y1: int
    x2: int
    y2: int


    @property
    def width(self) -> int:
        return self.x2 - self.x1

    @property
    def height(self) -> int:
        return self.y2 - self.y1

    def to_box(self, offset_x: int = 0, offset_y: int = 0) -> Box:
        box = Box(
            x=self.x1 + offset_x,
            y=self.y1 + offset_y,
            to_x=self.x2 + offset_x,
            to_y=self.y2 + offset_y,
        )
        box.name = self.cls_name
        box.confidence = self.confidence
        return box


class YoloDetector:
    """YOLO 检测器，默认使用项目根目录下的 models/yolo/best.pt。"""

    _model_cache: dict[str, object] = {}

    def __init__(self, model_path: str | None = None):
        root = Path(__file__).resolve().parents[2]
        if model_path:
            model_file = Path(model_path)
            if not model_file.is_absolute():
                model_file = root / model_file
        else:
            model_file = root / "models" / "yolo" / "best.pt"
        self.model_path = str(model_file)
        self.model = self._load_model(self.model_path)

    @classmethod
    def _load_model(cls, model_path: str):
        cached_model = cls._model_cache.get(model_path)
        if cached_model is not None:
            return cached_model

        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise ImportError("未安装 ultralytics，请先安装：pip install ultralytics") from exc

        model = YOLO(model_path)
        cls._model_cache[model_path] = model
        return model

    def detect(self, frame: np.ndarray, conf: float = 0.25) -> list[YoloDetection]:
        results = self.model.predict(source=frame, conf=conf, verbose=False)
        if not results:
            return []

        result = results[0]
        names = result.names or {}
        detections: list[YoloDetection] = []

        for box in result.boxes:
            x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
            cls_id = int(box.cls[0].item())
            confidence = float(box.conf[0].item())
            cls_name = str(names.get(cls_id, cls_id))
            detections.append(
                YoloDetection(
                    cls_id=cls_id,
                    cls_name=cls_name,
                    confidence=confidence,
                    x1=x1,
                    y1=y1,
                    x2=x2,
                    y2=y2,
                )
            )

        return detections
