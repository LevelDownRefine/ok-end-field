from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import numpy as np
import onnxruntime as ort
import cv2
from ok import Box


@dataclass(slots=True)
class OnnxDetection:
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
        box = Box(x=self.x1 + offset_x, y=self.y1 + offset_y, to_x=self.x2 + offset_x, to_y=self.y2 + offset_y)
        box.name = self.cls_name
        box.confidence = self.confidence
        return box


class OnnxYoloDetector:

    def __init__(self, model_path: str | None = None):

        root = Path(__file__).resolve().parents[2]

        if model_path:
            model_file = Path(model_path)
            if not model_file.is_absolute():
                model_file = root / model_file
        else:
            model_file = root / "models" / "onnx" / "best.onnx"

        self.model_path = str(model_file)

        self.session = ort.InferenceSession(self.model_path, providers=["CPUExecutionProvider"])

        self.input_name = self.session.get_inputs()[0].name
        self.input_shape = self.session.get_inputs()[0].shape

        self.output_names = [o.name for o in self.session.get_outputs()]

        self.img_size = self.input_shape[2]

    def preprocess(self, frame: np.ndarray):

        h, w = frame.shape[:2]

        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        img = cv2.resize(img, (self.img_size, self.img_size))

        img = img.astype(np.float32) / 255.0

        img = np.transpose(img, (2, 0, 1))[None]

        return img, w, h

    def nms(self, boxes, scores, iou_threshold=0.45):

        indices = cv2.dnn.NMSBoxes(boxes, scores, score_threshold=0.0, nms_threshold=iou_threshold)

        if len(indices) == 0:
            return []

        return indices.flatten()

    def detect(self, frame: np.ndarray, conf: float = 0.25):

        img, orig_w, orig_h = self.preprocess(frame)

        outputs = self.session.run(self.output_names, {self.input_name: img})

        preds = outputs[0]

        if preds.shape[1] < preds.shape[2]:
            preds = np.transpose(preds, (0, 2, 1))

        preds = preds[0]

        boxes = []
        scores = []
        class_ids = []

        for pred in preds:

            bbox = pred[:4]
            class_scores = pred[4:]

            cls_id = int(np.argmax(class_scores))
            score = class_scores[cls_id]

            if score < conf:
                continue

            x, y, w, h = bbox

            x1 = x - w / 2
            y1 = y - h / 2
            x2 = x + w / 2
            y2 = y + h / 2

            boxes.append([int(x1), int(y1), int(x2 - x1), int(y2 - y1)])

            scores.append(float(score))
            class_ids.append(cls_id)

        keep = self.nms(boxes, scores)

        detections: list[OnnxDetection] = []

        for i in keep:

            x, y, w, h = boxes[i]

            detections.append(
                OnnxDetection(
                    cls_id=class_ids[i],
                    cls_name=str(class_ids[i]),
                    confidence=scores[i],
                    x1=x,
                    y1=y,
                    x2=x + w,
                    y2=y + h,
                )
            )

        return detections
