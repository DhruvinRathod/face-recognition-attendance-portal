"""Train the portal's OpenCV LBPH recognition model from enrolled face samples."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FACES = ROOT / "data" / "faces"
MODELS = ROOT / "models"
MODEL = MODELS / "lbph_face_model.yml"
LABELS = MODELS / "labels.json"


def portal_students():
    sys.path.insert(0, str(ROOT))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "attendance_portal.settings")
    import django
    django.setup()
    from attendance.models import Student
    return {student.student_id: student for student in Student.objects.all()}


def main():
    if not hasattr(cv2, "face") or not hasattr(cv2.face, "LBPHFaceRecognizer_create"):
        raise RuntimeError("cv2.face is unavailable. Install opencv-contrib-python; remove conflicting OpenCV packages first.")
    MODELS.mkdir(exist_ok=True)
    enrolled = portal_students()
    enrolled_by_folder = {student.face_folder: student for student in enrolled.values() if student.face_folder}
    enrolled_by_id_lower = {student_id.lower(): student for student_id, student in enrolled.items()}
    images, targets, mapping = [], [], {}
    numeric = 0

    for folder in sorted(path for path in FACES.iterdir() if path.is_dir()):
        parts = folder.name.split("__", 1)
        files = sorted(folder.glob("*.png"))
        if len(parts) != 2 or len(files) < 20:
            print(f"Skipping {folder.name}: expected ID__name and at least 20 images")
            continue
        student_id = parts[0]
        # New samples are matched by the exact face_folder saved in the portal.
        # The ID fallback also supports older folders created by the standalone prototype.
        student = enrolled_by_folder.get(folder.name) or enrolled.get(student_id) or enrolled_by_id_lower.get(student_id.lower())
        if student is None:
            print(f"Skipping {folder.name}: no matching Student in the portal. Add/enroll the student first.")
            continue
        used = 0
        for file in files:
            image = cv2.imread(str(file), cv2.IMREAD_GRAYSCALE)
            if image is not None:
                images.append(cv2.resize(image, (200, 200)))
                targets.append(numeric)
                used += 1
        if used:
            mapping[str(numeric)] = {"student_id": student.student_id, "name": student.name, "samples": used}
            numeric += 1

    if not images:
        raise RuntimeError("No valid samples. Add a portal student, run register_face.py, then try again.")
    recognizer = cv2.face.LBPHFaceRecognizer_create(radius=1, neighbors=8, grid_x=8, grid_y=8, threshold=100.0)
    recognizer.train(images, np.array(targets, dtype=np.int32))
    recognizer.save(str(MODEL))
    LABELS.write_text(json.dumps(mapping, indent=2), encoding="utf-8")
    print(f"Trained {len(images)} images for {len(mapping)} person(s).")
    print(f"Saved: {MODEL} and {LABELS}")
    print("Restart the Django development server after retraining if it is already running.")


if __name__ == "__main__":
    main()
