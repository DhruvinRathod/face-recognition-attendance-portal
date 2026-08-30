from django.conf import settings
from django.db import models
from django.utils import timezone


class Student(models.Model):
    """A student whose attendance can be recorded; students have no portal login."""
    student_id = models.CharField(primary_key=True, max_length=40)
    name = models.CharField(max_length=120)
    email = models.EmailField(blank=True)
    face_folder = models.CharField(max_length=160, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["student_id"]

    def __str__(self) -> str:
        return f"{self.student_id} — {self.name}"


class Course(models.Model):
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=150)
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="courses")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["code"]

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"


class Enrollment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="enrollments")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["course", "student"], name="unique_course_student")]
        ordering = ["student__student_id"]

    def __str__(self) -> str:
        return f"{self.student} in {self.course}"


class AttendanceSession(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        FINALIZED = "FINALIZED", "Finalized"

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="sessions")
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="attendance_sessions")
    session_date = models.DateField(default=timezone.localdate)
    started_at = models.DateTimeField(auto_now_add=True)
    finalized_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.OPEN)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self) -> str:
        return f"{self.course.code} on {self.session_date} ({self.status})"


class AttendanceRecord(models.Model):
    class Status(models.TextChoices):
        PRESENT = "PRESENT", "Present"
        ABSENT = "ABSENT", "Absent"

    class Source(models.TextChoices):
        FACE = "FACE", "Face recognition"
        MANUAL = "MANUAL", "Teacher correction"
        SYSTEM = "SYSTEM", "Session initialization"
        DEMO = "DEMO", "Demo simulation"

    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name="records")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="attendance_records")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ABSENT)
    source = models.CharField(max_length=10, choices=Source.choices, default=Source.SYSTEM)
    recognition_distance = models.FloatField(null=True, blank=True)
    marked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["session", "student"], name="one_record_per_student_session")]
        ordering = ["student__student_id"]

    def mark_present(self, source: str, distance: float | None = None) -> bool:
        """Return True only when the record changes from absent to present."""
        changed = self.status != self.Status.PRESENT
        self.status = self.Status.PRESENT
        self.source = source
        self.recognition_distance = distance
        self.marked_at = timezone.now()
        self.save(update_fields=["status", "source", "recognition_distance", "marked_at"])
        return changed

    def __str__(self) -> str:
        return f"{self.student} — {self.status}"
