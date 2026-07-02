"""Read the locally trained OpenCV LBPH model and recognize one browser frame."""
from __future__ import annotations

import base64
import binascii
import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from django.conf import settings


class RecognitionError(RuntimeError):
    pass


@dataclass(frozen=True)
class RecognitionResult:
    matched: bool
    student_id: str | None = None
    name: str | None = None
    distance: float | None = None
    message: str = "Unknown face"


@lru_cache(maxsize=1)
def _assets():
    try:
        import cv2
        import numpy as np
    except ImportError as exc:
        raise RecognitionError("OpenCV and NumPy must be installed before live recognition can run.") from exc

    if not hasattr(cv2, "face") or not hasattr(cv2.face, "LBPHFaceRecognizer_create"):
        raise RecognitionError("cv2.face is missing. Install opencv-contrib-python, not opencv-python.")

    root = Path(settings.BASE_DIR)
    model_path = root / "models" / "lbph_face_model.yml"
    labels_path = root / "models" / "labels.json"
    if not model_path.exists() or not labels_path.exists():
        raise RecognitionError("No trained model found. Enroll a face and run: python src/train_model.py")

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(str(model_path))
    labels = json.loads(labels_path.read_text(encoding="utf-8"))
    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    if cascade.empty():
        raise RecognitionError("OpenCV Haar cascade could not be loaded.")
    return cv2, np, recognizer, labels, cascade


def clear_cached_model() -> None:
    """Useful after retraining during a development server session."""
    _assets.cache_clear()


def _decode_data_url(image_data_url: str) -> bytes:
    if not image_data_url.startswith("data:image/") or "," not in image_data_url:
        raise RecognitionError("The browser frame is not a valid image data URL.")
    try:
        payload = image_data_url.split(",", 1)[1]
        data = base64.b64decode(payload, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise RecognitionError("Could not decode the browser frame.") from exc
    if len(data) > settings.MAX_FRAME_BYTES:
        raise RecognitionError("The browser frame is too large.")
    return data


def recognize_data_url(image_data_url: str) -> RecognitionResult:
    cv2, np, recognizer, labels, cascade = _assets()
    raw = _decode_data_url(image_data_url)
    image = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise RecognitionError("OpenCV could not read the browser frame.")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(120, 120))
    if len(faces) == 0:
        return RecognitionResult(False, message="No face detected")

    x, y, w, h = max(faces, key=lambda face: face[2] * face[3])
    crop = cv2.equalizeHist(cv2.resize(gray[y:y+h, x:x+w], (200, 200)))
    label, distance = recognizer.predict(crop)
    person = labels.get(str(label))
    if person is None or distance > float(settings.FACE_RECOGNITION_THRESHOLD):
        return RecognitionResult(False, distance=float(distance), message="Unknown face")

    return RecognitionResult(
        True,
        student_id=str(person["student_id"]),
        name=str(person["name"]),
        distance=float(distance),
        message="Face matched",
    )
