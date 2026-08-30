import json
from unittest.mock import patch

from django.contrib.auth.models import Group, User
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import AttendanceRecord, AttendanceSession, Course, Enrollment, Student
from .permissions import TEACHERS_GROUP
from .services.recognition import RecognitionResult


class AttendancePortalTests(TestCase):
    def setUp(self):
        cache.clear()
        teachers, _ = Group.objects.get_or_create(name=TEACHERS_GROUP)
        self.teacher = User.objects.create_user("teacher", password="SafePass123!")
        self.teacher.groups.add(teachers)
        self.non_teacher = User.objects.create_user("studentuser", password="SafePass123!")
        self.course = Course.objects.create(code="AI-101", name="Introduction to AI", teacher=self.teacher)
        self.student = Student.objects.create(student_id="S001", name="Demo Student")
        Enrollment.objects.create(course=self.course, student=self.student)

    def start_open_session(self):
        self.client.force_login(self.teacher)
        response = self.client.post(reverse("start_session", args=[self.course.id]))
        self.assertEqual(response.status_code, 302)
        return AttendanceSession.objects.get()

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_logged_in_non_teacher_cannot_view_dashboard(self):
        self.client.force_login(self.non_teacher)
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 403)

    def test_starting_a_session_creates_absent_record_for_every_enrolled_student(self):
        session = self.start_open_session()
        record = AttendanceRecord.objects.get(session=session, student=self.student)
        self.assertEqual(record.status, AttendanceRecord.Status.ABSENT)
        self.assertEqual(record.source, AttendanceRecord.Source.SYSTEM)

    @patch("attendance.views.recognize_data_url")
    def test_three_confirmed_face_frames_mark_student_present_once(self, mock_recognize):
        session = self.start_open_session()
        mock_recognize.return_value = RecognitionResult(
            matched=True, student_id=self.student.student_id, name=self.student.name, distance=39.1
        )
        url = reverse("recognize_frame", args=[session.id])

        for expected_count in (1, 2):
            response = self.client.post(url, data=json.dumps({"image": "data:image/jpeg;base64,AA=="}), content_type="application/json")
            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.json()["confirmed"])
            self.assertEqual(response.json()["count"], expected_count)

        response = self.client.post(url, data=json.dumps({"image": "data:image/jpeg;base64,AA=="}), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["attendance_status"], "marked_present")
        record = AttendanceRecord.objects.get(session=session, student=self.student)
        self.assertEqual(record.status, AttendanceRecord.Status.PRESENT)
        self.assertEqual(record.source, AttendanceRecord.Source.FACE)

        response = self.client.post(url, data=json.dumps({"image": "data:image/jpeg;base64,AA=="}), content_type="application/json")
        self.assertEqual(response.json()["attendance_status"], "already_present")
        self.assertEqual(AttendanceRecord.objects.filter(session=session, student=self.student).count(), 1)

    @override_settings(DEMO_MODE=True, DEMO_USERNAME="teacher", DEMO_PASSWORD="SafePass123!")
    def test_demo_login_uses_preloaded_teacher(self):
        response = self.client.post(reverse("demo_login"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("dashboard"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.teacher.id)

    @override_settings(DEMO_MODE=True)
    def test_demo_simulation_marks_student_present_without_biometric_processing(self):
        session = self.start_open_session()
        response = self.client.post(reverse("simulate_recognition", args=[session.id]))
        self.assertEqual(response.status_code, 302)

        record = AttendanceRecord.objects.get(session=session, student=self.student)
        self.assertEqual(record.status, AttendanceRecord.Status.PRESENT)
        self.assertEqual(record.source, AttendanceRecord.Source.DEMO)
        self.assertIsNone(record.recognition_distance)

        blocked = self.client.post(
            reverse("recognize_frame", args=[session.id]),
            data=json.dumps({"image": "data:image/jpeg;base64,AA=="}),
            content_type="application/json",
        )
        self.assertEqual(blocked.status_code, 403)
        self.assertIn("disabled", blocked.json()["message"])

    def test_teacher_can_manually_correct_and_export_final_report(self):
        session = self.start_open_session()
        update = self.client.post(
            reverse("mark_record_manually", args=[session.id, self.student.student_id]), {"status": "PRESENT"}
        )
        self.assertEqual(update.status_code, 302)
        record = AttendanceRecord.objects.get(session=session, student=self.student)
        self.assertEqual(record.status, AttendanceRecord.Status.PRESENT)
        self.assertEqual(record.source, AttendanceRecord.Source.MANUAL)

        finalize = self.client.post(reverse("finalize_session", args=[session.id]))
        self.assertEqual(finalize.status_code, 302)
        session.refresh_from_db()
        self.assertEqual(session.status, AttendanceSession.Status.FINALIZED)

        export = self.client.get(reverse("export_session_csv", args=[session.id]))
        self.assertEqual(export.status_code, 200)
        self.assertEqual(export["Content-Type"], "text/csv")
        self.assertIn("Demo Student", export.content.decode("utf-8"))
