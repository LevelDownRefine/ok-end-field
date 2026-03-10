from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


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


class YoloExample:
    """本项目的最小 YOLO 接入示例。

    用法：
    1. 安装依赖：pip install ultralytics
    2. 准备模型：可使用 yolov8n.pt 或自训模型
    3. 传入 OpenCV 的 BGR 图像进行检测
    """

    def __init__(self, model_path: str = "yolov8n.pt"):
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise ImportError(
                "未安装 ultralytics，请先安装：pip install ultralytics"
            ) from exc

        self.model = YOLO(model_path)

    def detect(self, frame: np.ndarray, conf: float = 0.25) -> list[YoloDetection]:
        """对单帧图像做检测。"""
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

    @staticmethod
    def draw_detections(frame: np.ndarray, detections: list[YoloDetection]) -> np.ndarray:
        """在图像上绘制检测框。"""
        output = frame.copy()
        for det in detections:
            cv2.rectangle(output, (det.x1, det.y1), (det.x2, det.y2), (0, 255, 0), 2)
            label = f"{det.cls_name} {det.confidence:.2f}"
            cv2.putText(
                output,
                label,
                (det.x1, max(det.y1 - 8, 0)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                1,
                cv2.LINE_AA,
            )
        return output


def demo_detect_image(
    image_path: str,
    model_path: str,
    output_path: str | None = None,
) -> list[YoloDetection]:
    """读取单张图片并输出可视化结果。"""
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"无法读取图片: {image_path}")

    detector = YoloExample(model_path=model_path)
    detections = detector.detect(image)

    if output_path:
        rendered = detector.draw_detections(image, detections)
        cv2.imwrite(output_path, rendered)

    return detections


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[2]
    input_path = repo_root / "yolo_tem" / "cap_20260310_224923_0001.png"
    output_path = repo_root / "yolo_tem"/ "yolo_demo_output.png"

    detections = demo_detect_image(image_path=str(input_path), model_path="models/yolo/best.pt", output_path=str(output_path))

    print(f"检测到 {len(detections)} 个目标")
    for det in detections:
        print(
            f"- {det.cls_name}: conf={det.confidence:.2f}, "
            f"box=({det.x1}, {det.y1}, {det.x2}, {det.y2})"
        )
