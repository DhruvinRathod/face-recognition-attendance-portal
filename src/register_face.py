"""Capture face samples and sync the enrolled person to the Django portal."""
from __future__ import annotations

import argparse
import os
import re
import sys
import time
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parents[1]
FACES_DIR = ROOT / "data" / "faces"


def source(value: str):
    return int(value) if value.isdigit() else value


def slug(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", value.strip()).strip("_").lower() or "student"


def largest(faces):
    return max(faces, key=lambda f: f[2] * f[3]) if len(faces) else None


def sync_portal_student(student_id: str, name: str, folder_name: str) -> None:
    """Create/update the corresponding Student model after migrations exist."""
    sys.path.insert(0, str(ROOT))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "attendance_portal.settings")
    import django
    django.setup()
    from attendance.models import Student

    student, _ = Student.objects.get_or_create(student_id=student_id, defaults={"name": name})
    student.name = name
    student.face_folder = folder_name
    student.save(update_fields=["name", "face_folder"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--student-id", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--samples", type=int, default=70)
    parser.add_argument("--source", default="0")
    args = parser.parse_args()
    if args.samples < 20:
        raise ValueError("Use at least 20 samples; 50–80 is recommended.")

    folder = f"{slug(args.student_id)}__{slug(args.name)}"
    out = FACES_DIR / folder
    out.mkdir(parents=True, exist_ok=True)
    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    cap = cv2.VideoCapture(source(args.source))
    if not cap.isOpened():
        raise RuntimeError("Camera could not open. Try --source 1 or check permissions.")

    count, last = 0, 0.0
    print("Move your face slightly; q quits. Only one consenting person should be in the frame.")
    try:
        while count < args.samples:
            ok, frame = cap.read()
            if not ok:
                break
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            face = largest(cascade.detectMultiScale(gray, 1.2, 5, minSize=(120, 120)))
            message = "No face detected"
            if face is not None:
                x, y, w, h = face
                crop = cv2.equalizeHist(cv2.resize(gray[y:y+h, x:x+w], (200, 200)))
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                message = "Face detected — move slightly"
                if time.time() - last > 0.12:
                    count += 1
                    last = time.time()
                    cv2.imwrite(str(out / f"face_{count:03d}.png"), crop)
            cv2.putText(frame, f"Samples {count}/{args.samples} | {message}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, .62, (255, 255, 255), 2)
            cv2.imshow("Register face — q to quit", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()

    if count < 20:
        raise RuntimeError(f"Only {count} samples captured. Capture at least 20 before training.")
    sync_portal_student(args.student_id, args.name, folder)
    print(f"Saved {count} samples to {out}")
    print("Portal student synced. Next: python src/train_model.py")


if __name__ == "__main__":
    main()
