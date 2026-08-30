from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("attendance/history/", views.attendance_history, name="attendance_history"),
    path("courses/new/", views.course_create, name="course_create"),
    path("students/new/", views.student_create, name="student_create"),
    path("courses/<int:course_id>/start/", views.start_session, name="start_session"),
    path("sessions/<int:session_id>/live/", views.live_session, name="live_session"),
    path("sessions/<int:session_id>/recognize/", views.recognize_frame, name="recognize_frame"),
    path("sessions/<int:session_id>/simulate/", views.simulate_recognition, name="simulate_recognition"),
    path("sessions/<int:session_id>/simulate-unknown/", views.simulate_unknown_face, name="simulate_unknown_face"),
    path("sessions/<int:session_id>/records/<str:student_id>/mark/", views.mark_record_manually, name="mark_record_manually"),
    path("sessions/<int:session_id>/finalize/", views.finalize_session, name="finalize_session"),
    path("sessions/<int:session_id>/report/", views.session_report, name="session_report"),
    path("sessions/<int:session_id>/export.csv", views.export_session_csv, name="export_session_csv"),
]
