# Face Recognition Attendance Portal

A **teacher-only student attendance management portal** for a local academic demo. An authenticated teacher can create courses, enroll students, open a live attendance session, use the browser camera for face recognition, manually correct the roster, finalize the session, and export a CSV report.

> **Prototype only.** This project is not a production identity-verification or surveillance system. Use only with informed consent, give students a manual attendance alternative, and never use its automated result as the sole basis for a high-impact decision.

## What is included

- Teacher login with a `Teachers` role; non-teacher users receive `403 Forbidden`.
- Teacher dashboard for creating courses and adding/enrolling students.
- Session-based attendance: each attendance session starts with its enrolled students as **Absent**.
- Browser-camera live attendance: the live page sends a small image frame to the local Django server for OpenCV LBPH recognition.
- Consecutive-frame confirmation: a face must match **3 consecutive frames** before the record becomes Present.
- One record per student per session; repeated recognition cannot create duplicate records.
- Teacher manual correction before finalization.
- Finalized report page and CSV export.
- Webcam face enrollment and local LBPH model training scripts.
- Automated tests for authentication, teacher authorization, attendance creation, three-frame recognition confirmation, manual correction, finalization, and CSV export.

## Technology stack

- **Backend / portal:** Django
- **Authentication:** Django built-in auth + `Teachers` group
- **Database:** SQLite
- **Face recognition:** OpenCV Contrib, Haar face detection, LBPH recognizer
- **Frontend:** HTML, CSS, vanilla JavaScript, browser `getUserMedia()` camera access

## Project layout

```text
attendance/                         Django application
  models.py                         Student, Course, Enrollment, Session, Record
  views.py                          Teacher-only portal routes and APIs
  services/recognition.py           Uses the trained LBPH model on browser frames
  management/commands/
    create_demo_data.py             Creates a safe local demo teacher/course/students
attendance_portal/                  Django settings and URLs
templates/                          Login and portal pages
static/portal.css                   Portal styling
src/register_face.py                Webcam enrollment + Student sync
src/train_model.py                  Creates models/lbph_face_model.yml
models/                             Trained face model (ignored by Git)
data/faces/                         Face samples (ignored by Git)
data/portal.db                      Portal database (ignored by Git)
```

## Local setup (Windows PowerShell)

```powershell
cd E:\Projects\face-recognition-attendance-system\face-recognition-attendance-system
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py create_demo_data --username teacher --password "TeacherDemo123!"
python manage.py runserver
```

Open this page in Chrome or Edge:

```text
http://127.0.0.1:8000/login/
```

For the local demo, log in with:

```text
Username: teacher
Password: TeacherDemo123!
```

Change the password before any real use. The demo command creates:

```text
Course: AI-101 — Introduction to Artificial Intelligence
Students: S001 and S002
```

## First live recognition test

### 1. Enroll one consented person

Use the same student ID that exists in the portal. For the included demo, use `S001`.

```powershell
python src/register_face.py --student-id S001 --name "Your Name" --samples 70
```

Move slightly during capture. Press `q` only after at least 20 samples have been captured.

### 2. Train the model

```powershell
python src/train_model.py
```

This creates:

```text
models/lbph_face_model.yml
models/labels.json
```

If Django is already running, stop it with `Ctrl + C` and run `python manage.py runserver` again after retraining.

### 3. Start a live attendance session

1. Log in as the teacher.
2. Click **Start live attendance** for `AI-101`.
3. Click **Start camera** and allow browser camera permission.
4. Keep the enrolled face visible for about 3 seconds.
5. The screen should move from `Recognizing … 1/3` to `Attendance marked present`.
6. Test the **manual correction** controls if the match is missed.
7. Click **Finalize attendance** and then **Download CSV**.

For local development, browsers allow camera access through `localhost` / `127.0.0.1`. A deployed version requires HTTPS for camera permission.

## Add your own class and students

1. Use **Create course** on the dashboard.
2. Use **Add student** and tick the courses in which the student is enrolled.
3. Run the enrollment script with that exact student ID.
4. Re-run `python src/train_model.py` whenever new face samples are added.
5. Start a session only after students are enrolled in that course.

## Tests

Run the portal test suite:

```powershell
python manage.py test
```

The test suite does not need a real camera or a trained face model; it mocks the recognition service and verifies the portal rules.

## OpenCV check

The live-recognition module needs the **contrib** package because LBPH lives under `cv2.face`:

```powershell
python -c "import cv2; print(cv2.__version__); print(hasattr(cv2, 'face'))"
```

The final line must be `True`. If it is `False`:

```powershell
pip uninstall -y opencv-python opencv-python-headless opencv-contrib-python
pip install -r requirements.txt
```

## Note about the original command-line script

`src/live_attendance.py` is retained as the original standalone webcam/video prototype. For the full teacher portal, use `python manage.py runserver` and start attendance from the dashboard instead. Portal attendance is stored in `data/portal.db`; the legacy script uses its own local database.

## Important limitations

- This demo recognizes only the **largest detected face** in a frame. It is designed for one person standing in front of the camera, not automatic whole-class scanning.
- It does **not** include liveness detection. A production system would need spoof-resistance measures and much stronger evaluation.
- LBPH accuracy is sensitive to lighting, pose, camera quality, and the number/quality of enrollment samples.
- The Django development server, SQLite, and local cache are appropriate for a portfolio demo, not a real university deployment.
- Do not commit face samples, trained models, SQLite databases, passwords, or CSV attendance exports. The `.gitignore` excludes them.

## Suggested GitHub description

> A role-based Django attendance management portal where authenticated teachers conduct local live face-recognition sessions, review and correct attendance, finalize class records, and export reports.
