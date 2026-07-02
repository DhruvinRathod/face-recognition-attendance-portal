# Face Recognition Attendance Portal

A role-based student attendance management portal that allows authenticated teachers to conduct live face-recognition attendance sessions, review detected students, manually correct records, and export attendance reports.

## Features

* Teacher-only login and protected dashboard
* Course and student management
* Browser-based live camera attendance
* Face recognition using OpenCV
* Attendance confirmation after repeated face detection
* One attendance record per student per session
* Manual teacher correction before finalizing attendance
* Attendance session history
* CSV attendance report export
* SQLite database for local development

## Tech Stack

* **Backend:** Python, Django
* **Frontend:** HTML, CSS, Bootstrap, JavaScript
* **Face Recognition:** OpenCV, LBPH Face Recognizer
* **Database:** SQLite
* **Authentication:** Django built-in authentication
* **Testing:** Django test framework

## Project Structure

```text
face-recognition-attendance-portal/
├── manage.py
├── requirements.txt
├── accounts/                  # Teacher authentication and access control
├── attendance/                # Courses, students, sessions, reports
├── face_data/                 # Registered face images
├── trained_models/            # Trained face-recognition model
├── src/
│   ├── register_face.py
│   ├── train_model.py
│   └── live_attendance.py
├── static/
├── templates/
└── README.md
```

## Installation

Clone the repository:

```bash
git clone https://github.com/YOUR-USERNAME/face-recognition-attendance-portal.git
cd face-recognition-attendance-portal
```

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Apply database migrations:

```bash
python manage.py migrate
```

Create demo teacher and sample course data:

```bash
python manage.py create_demo_data --username teacher --password "TeacherDemo123!"
```

Start the application:

```bash
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/login/
```

Demo login credentials:

```text
Username: teacher
Password: TeacherDemo123!
```

## Face Registration and Training

Register a student face:

```bash
python src/register_face.py --student-id S001 --name "Student Name" --samples 70
```

Train the recognition model:

```bash
python src/train_model.py
```

Restart the Django server after training the model.

## Attendance Workflow

1. Teacher logs in to the portal.
2. Teacher selects a course and creates an attendance session.
3. Teacher opens the live attendance page.
4. Browser camera captures video frames.
5. The portal detects and recognizes enrolled student faces.
6. A student is marked present only after repeated recognition.
7. Teacher reviews and manually corrects records where needed.
8. Teacher finalizes the attendance session.
9. Attendance can be exported as a CSV report.

## Testing

Run automated tests:

```bash
python manage.py test
```

## Privacy and Ethical Use

This project is intended for academic demonstration and controlled testing only. Use facial data only with explicit consent. Do not deploy it in a real educational institution without legal review, privacy safeguards, and appropriate biometric-data policies.

## Future Improvements

* Admin dashboard for managing teachers and departments
* MySQL or PostgreSQL deployment
* Face anti-spoofing and liveness detection
* Email notifications for attendance reports
* Student attendance analytics dashboard
* Docker deployment
* Cloud-based secure image storage

## Author

Shalini Nanjunda
M.Sc. Artificial Intelligence Student
GitHub: https://github.com/YOUR-USERNAME
