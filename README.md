# Face Recognition Attendance Portal

A **role-based Django attendance management portal** where authenticated teachers create courses, enroll students, run attendance sessions, review and correct records, finalize sessions, and export CSV reports. The local prototype also includes consent-based OpenCV/LBPH face recognition.

> **Prototype only.** This project is not a production identity-verification or surveillance system. Use biometric features only with informed consent, provide a manual attendance alternative, and never use automated recognition as the sole basis for a high-impact decision.

## Live demo

**[Open the hosted demo →](https://face-attendance-demo.onrender.com)**

The public demo uses a **safe hosted mode** for portfolio review:

- one-click entry with a preloaded teacher account;
- synthetic course and student data;
- the complete attendance workflow: start session → mark attendance → correct roster → finalize → export CSV;
- an explicit **Simulate face match** action that demonstrates recognition-driven application flow without uploading or processing a visitor's face;
- real camera/LBPH recognition remains available in the local consent-based prototype and is intentionally disabled on the public demo.

The repository includes a Render Blueprint (`render.yaml`) for reproducible deployment of the Django demo.

## What is included

- Teacher login with a `Teachers` role; non-teacher users receive `403 Forbidden`.
- Teacher dashboard for creating courses and adding/enrolling students.
- Session-based attendance: each attendance session starts with its enrolled students as **Absent**.
- Browser-camera live attendance for local use: the page sends a small image frame to the Django server for OpenCV LBPH recognition.
- Consecutive-frame confirmation: a face must match **3 consecutive frames** before the record becomes Present.
- One record per student per session; repeated recognition cannot create duplicate records.
- Teacher manual correction before finalization.
- Finalized report page and CSV export.
- Webcam face enrollment and local LBPH model training scripts.
- Hosted demo mode that does not process public biometric data.
- Automated tests for authentication, teacher authorization, attendance creation, recognition confirmation, demo simulation, manual correction, finalization, and CSV export.

## Technology stack

- **Backend:** Django / Python
- **Authentication & authorization:** Django auth + `Teachers` group
- **Database:** SQLite for the portfolio prototype/demo
- **Face recognition:** OpenCV Contrib, Haar face detection, LBPH recognizer
- **Frontend:** HTML, CSS, vanilla JavaScript, browser `getUserMedia()` camera access
- **Hosted demo:** Gunicorn + WhiteNoise + Render Blueprint
- **CI:** GitHub Actions

## Project layout

```text
attendance/                         Django application
  models.py                         Student, Course, Enrollment, Session, Record
  views.py                          Teacher-only portal routes and demo workflow
  services/recognition.py           Uses the trained LBPH model on browser frames
  management/commands/
    create_demo_data.py             Creates synthetic demo teacher/course/students
attendance_portal/                  Django settings and URLs
templates/                          Login and shared portal templates
static/portal.css                   Portal styling
src/register_face.py                Local webcam enrollment + Student sync
src/train_model.py                  Creates models/lbph_face_model.yml
models/                             Trained face model (ignored by Git)
data/faces/                         Face samples (ignored by Git)
data/portal.db                      Portal database (ignored by Git)
render.yaml                         Hosted demo configuration
requirements-demo.txt               Lightweight hosted-demo dependencies
start_demo.sh                       Migrate, seed demo data, start Gunicorn
```

## Local setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py create_demo_data --username teacher --password "TeacherDemo123!"
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/login/
```

For a local demo:

```text
Username: teacher
Password: TeacherDemo123!
```

The demo command creates:

```text
Course: AI-101 — Introduction to Artificial Intelligence
Students: S001 and S002
```

## Hosted demo mode

For production-style demo hosting, set:

```text
DEMO_MODE=true
SECRET_KEY=<secure random value>
```

The hosted mode automatically disables the camera-recognition endpoint and exposes a simulation control instead. This preserves the application workflow without collecting biometric data from public visitors.

The included Render configuration installs `requirements-demo.txt`, collects static assets, migrates the database, creates synthetic demo data and starts Gunicorn. The SQLite database is intentionally disposable for this portfolio demo and may reset when a free hosting instance restarts.

## Local face-recognition test

### 1. Enroll one consented person

Use the same student ID that exists in the portal. For the included demo, use `S001`.

```powershell
python src/register_face.py --student-id S001 --name "Your Name" --samples 70
```

### 2. Train the model

```powershell
python src/train_model.py
```

This creates:

```text
models/lbph_face_model.yml
models/labels.json
```

### 3. Start a live attendance session

1. Log in as the teacher.
2. Click **Start live attendance** for `AI-101`.
3. Click **Start camera** and allow browser camera permission.
4. Keep the enrolled face visible for about 3 seconds.
5. The screen progresses from `Recognizing … 1/3` to `Attendance marked present`.
6. Review or use the manual correction controls.
7. Finalize attendance and download the CSV report.

For local development, browsers allow camera access through `localhost` / `127.0.0.1`. A non-demo deployed camera workflow requires HTTPS.

## Tests

Run the Django test suite:

```powershell
python manage.py test attendance
```

The test suite does not require a real camera or trained face model; recognition is mocked where appropriate. GitHub Actions also checks migrations and runs the Django tests on pull requests and pushes to `main`.

## Important limitations

- The local recognition prototype recognizes only the **largest detected face** in a frame; it is not whole-class scanning.
- It does **not** include liveness detection or production-grade biometric evaluation.
- LBPH accuracy is sensitive to lighting, pose, camera quality, and enrollment samples.
- SQLite and the lightweight hosted configuration are appropriate for a portfolio demo, not a real university deployment.
- The public hosted demo deliberately uses synthetic records and simulated recognition.
- Do not commit face samples, trained models, databases, passwords, or CSV attendance exports. The `.gitignore` excludes these artifacts.

## Suggested GitHub description

> Role-based Django attendance portal with session workflows, CSV reporting, a consent-based OpenCV/LBPH local prototype, and a safe hosted demo.
