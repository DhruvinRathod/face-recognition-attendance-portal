from __future__ import annotations

import csv
import io
import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout
from django.core.cache import cache
from django.db import transaction
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import CourseForm, StudentForm
from .models import AttendanceRecord, AttendanceSession, Course, Enrollment, Student
from .permissions import teacher_required
from .services.recognition import RecognitionError, recognize_data_url


def logout_view(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        logout(request)
    return redirect("login")


@require_POST
def demo_login(request: HttpRequest) -> HttpResponse:
    """One-click login for the synthetic public portfolio demo only."""
    if not settings.DEMO_MODE:
        raise Http404

    user = authenticate(
        request,
        username=settings.DEMO_USERNAME,
        password=settings.DEMO_PASSWORD,
    )
    if user is None:
        messages.error(request, "The demo account is not ready yet. Please try again shortly.")
        return redirect("login")

    auth_login(request, user)
    messages.success(request, "Recruiter demo opened. All students and attendance data here are synthetic.")
    return redirect("dashboard")


def _teacher_course_or_404(user, course_id: int) -> Course:
    return get_object_or_404(Course, pk=course_id, teacher=user)


def _teacher_session_or_404(user, session_id: int) -> AttendanceSession:
    return get_object_or_404(
        AttendanceSession.objects.select_related("course", "teacher").prefetch_related("records__student"),
        pk=session_id,
        teacher=user,
    )


@teacher_required
def dashboard(request: HttpRequest) -> HttpResponse:
    courses = Course.objects.filter(teacher=request.user).prefetch_related("enrollments")
    sessions = AttendanceSession.objects.filter(teacher=request.user).select_related("course").prefetch_related("records")[:8]
    return render(
        request,
        "attendance/dashboard.html",
        {"courses": courses, "sessions": sessions, "demo_mode": settings.DEMO_MODE},
    )


@teacher_required
def course_create(request: HttpRequest) -> HttpResponse:
    form = CourseForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        course = form.save(commit=False)
        course.teacher = request.user
        course.save()
        messages.success(request, f"Course {course.code} was created.")
        return redirect("dashboard")
    return render(request, "attendance/form.html", {"form": form, "title": "Create a course", "submit_label": "Create course"})


@teacher_required
def student_create(request: HttpRequest) -> HttpResponse:
    form = StudentForm(request.POST or None, teacher=request.user)
    if request.method == "POST" and form.is_valid():
        student = form.save()
        for course in form.cleaned_data["courses"]:
            Enrollment.objects.get_or_create(course=course, student=student)
        messages.success(request, f"Student {student.name} was added.")
        return redirect("dashboard")
    return render(request, "attendance/form.html", {"form": form, "title": "Add a student", "submit_label": "Add student"})


@require_POST
@teacher_required
def start_session(request: HttpRequest, course_id: int) -> HttpResponse:
    course = _teacher_course_or_404(request.user, course_id)
    with transaction.atomic():
        session = AttendanceSession.objects.create(course=course, teacher=request.user)
        records = [
            AttendanceRecord(
                session=session,
                student=enrollment.student,
                status=AttendanceRecord.Status.ABSENT,
                source=AttendanceRecord.Source.SYSTEM,
            )
            for enrollment in course.enrollments.select_related("student")
        ]
        AttendanceRecord.objects.bulk_create(records, ignore_conflicts=True)

    if settings.DEMO_MODE:
        messages.info(request, "Attendance session started. Use the safe demo control to simulate recognition.")
    else:
        messages.info(request, "Attendance session started. Start the camera when you are ready.")
    return redirect("live_session", session_id=session.id)


@teacher_required
def live_session(request: HttpRequest, session_id: int) -> HttpResponse:
    session = _teacher_session_or_404(request.user, session_id)
    if session.status == AttendanceSession.Status.FINALIZED:
        return redirect("session_report", session_id=session.id)
    records = session.records.select_related("student").order_by("student__student_id")
    return render(
        request,
        "attendance/live_session.html",
        {
            "session": session,
            "records": records,
            "confirmation_frames": settings.FACE_CONFIRMATION_FRAMES,
            "demo_mode": settings.DEMO_MODE,
        },
    )


def _next_confirmation(session_id: int, student_id: str) -> int:
    """Track consecutive matched frames in Django's local cache for this prototype."""
    key = f"attendance-confirmation:{session_id}"
    state = cache.get(key, {"student_id": None, "count": 0})
    if state.get("student_id") == student_id:
        state["count"] = int(state.get("count", 0)) + 1
    else:
        state = {"student_id": student_id, "count": 1}
    cache.set(key, state, timeout=60)
    return state["count"]


def _reset_confirmation(session_id: int) -> None:
    cache.delete(f"attendance-confirmation:{session_id}")


@require_POST
@teacher_required
def simulate_recognition(request: HttpRequest, session_id: int) -> HttpResponse:
    """Demonstrate the attendance workflow without collecting public biometric data."""
    if not settings.DEMO_MODE:
        raise Http404

    session = _teacher_session_or_404(request.user, session_id)
    if session.status != AttendanceSession.Status.OPEN:
        messages.error(request, "This attendance session has already been finalized.")
        return redirect("session_report", session_id=session.id)

    record = (
        session.records.select_related("student")
        .filter(status=AttendanceRecord.Status.ABSENT)
        .order_by("student__student_id")
        .first()
    )
    if record is None:
        messages.info(request, "All demo students are already marked present. You can finalize the session or change the roster manually.")
        return redirect("live_session", session_id=session.id)

    record.mark_present(AttendanceRecord.Source.DEMO)
    messages.success(
        request,
        f"Simulated recognition matched {record.student.name}. No camera image or biometric data was processed.",
    )
    return redirect("live_session", session_id=session.id)


@require_POST
@teacher_required
def recognize_frame(request: HttpRequest, session_id: int) -> JsonResponse:
    session = _teacher_session_or_404(request.user, session_id)
    if session.status != AttendanceSession.Status.OPEN:
        return JsonResponse({"ok": False, "message": "This attendance session has already been finalized."}, status=409)

    if settings.DEMO_MODE:
        return JsonResponse(
            {
                "ok": False,
                "message": "Live biometric recognition is disabled on the public portfolio demo. Use the simulation control instead.",
            },
            status=403,
        )

    try:
        payload = json.loads(request.body.decode("utf-8"))
        image_data_url = payload["image"]
    except (UnicodeDecodeError, json.JSONDecodeError, KeyError):
        return JsonResponse({"ok": False, "message": "A valid JSON body containing an image is required."}, status=400)

    try:
        result = recognize_data_url(image_data_url)
    except RecognitionError as exc:
        return JsonResponse({"ok": False, "message": str(exc)}, status=422)

    if not result.matched or result.student_id is None:
        _reset_confirmation(session.id)
        return JsonResponse({"ok": True, "recognized": False, "message": result.message, "distance": result.distance})

    record = session.records.select_related("student").filter(student_id=result.student_id).first()
    if record is None:
        _reset_confirmation(session.id)
        return JsonResponse({"ok": True, "recognized": False, "message": f"{result.name} is not enrolled in {session.course.code}.", "distance": result.distance})

    if record.status == AttendanceRecord.Status.PRESENT:
        _reset_confirmation(session.id)
        return JsonResponse(
            {
                "ok": True,
                "recognized": True,
                "student_id": result.student_id,
                "name": record.student.name,
                "distance": result.distance,
                "confirmed": True,
                "attendance_status": "already_present",
                "message": f"Already marked present: {record.student.name}",
            }
        )

    count = _next_confirmation(session.id, result.student_id)
    if count < settings.FACE_CONFIRMATION_FRAMES:
        return JsonResponse(
            {
                "ok": True,
                "recognized": True,
                "student_id": result.student_id,
                "name": record.student.name,
                "distance": result.distance,
                "confirmed": False,
                "count": count,
                "message": f"Recognizing {record.student.name}: {count}/{settings.FACE_CONFIRMATION_FRAMES}",
            }
        )

    record.mark_present(AttendanceRecord.Source.FACE, result.distance)
    _reset_confirmation(session.id)
    return JsonResponse(
        {
            "ok": True,
            "recognized": True,
            "student_id": result.student_id,
            "name": record.student.name,
            "distance": result.distance,
            "confirmed": True,
            "attendance_status": "marked_present",
            "message": f"Attendance marked present: {record.student.name}",
        }
    )


@require_POST
@teacher_required
def mark_record_manually(request: HttpRequest, session_id: int, student_id: str) -> HttpResponse:
    session = _teacher_session_or_404(request.user, session_id)
    if session.status != AttendanceSession.Status.OPEN:
        messages.error(request, "Finalized sessions cannot be changed.")
        return redirect("session_report", session_id=session.id)
    record = get_object_or_404(AttendanceRecord, session=session, student_id=student_id)
    requested_status = request.POST.get("status")
    if requested_status not in AttendanceRecord.Status.values:
        return HttpResponseBadRequest("Invalid attendance status.")
    record.status = requested_status
    record.source = AttendanceRecord.Source.MANUAL
    record.recognition_distance = None
    record.marked_at = timezone.now()
    record.save(update_fields=["status", "source", "recognition_distance", "marked_at"])
    messages.success(request, f"Updated {record.student.name} to {record.get_status_display()}.")
    return redirect("live_session", session_id=session.id)


@require_POST
@teacher_required
def finalize_session(request: HttpRequest, session_id: int) -> HttpResponse:
    session = _teacher_session_or_404(request.user, session_id)
    if session.status == AttendanceSession.Status.OPEN:
        session.status = AttendanceSession.Status.FINALIZED
        session.finalized_at = timezone.now()
        session.save(update_fields=["status", "finalized_at"])
        _reset_confirmation(session.id)
        messages.success(request, "Attendance was finalized. You can now export the report.")
    return redirect("session_report", session_id=session.id)


@teacher_required
def session_report(request: HttpRequest, session_id: int) -> HttpResponse:
    session = _teacher_session_or_404(request.user, session_id)
    records = session.records.select_related("student").order_by("student__student_id")
    return render(request, "attendance/session_report.html", {"session": session, "records": records})


@teacher_required
def export_session_csv(request: HttpRequest, session_id: int) -> HttpResponse:
    session = _teacher_session_or_404(request.user, session_id)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["course_code", "course_name", "session_date", "student_id", "student_name", "status", "source", "marked_at", "recognition_distance"])
    for record in session.records.select_related("student").order_by("student__student_id"):
        writer.writerow(
            [
                session.course.code,
                session.course.name,
                session.session_date,
                record.student.student_id,
                record.student.name,
                record.status,
                record.source,
                record.marked_at.isoformat() if record.marked_at else "",
                record.recognition_distance or "",
            ]
        )
    response = HttpResponse(output.getvalue(), content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{session.course.code}_{session.session_date}_attendance.csv"'
    return response
