from django.contrib import admin
from .models import AttendanceRecord, AttendanceSession, Course, Enrollment, Student


class EnrollmentInline(admin.TabularInline):
    model = Enrollment
    extra = 0


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "teacher")
    list_filter = ("teacher",)
    search_fields = ("code", "name")
    inlines = [EnrollmentInline]


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("student_id", "name", "email", "face_folder")
    search_fields = ("student_id", "name", "email")


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ("course", "teacher", "session_date", "status", "started_at")
    list_filter = ("status", "session_date")


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ("session", "student", "status", "source", "marked_at")
    list_filter = ("status", "source")
    search_fields = ("student__student_id", "student__name")
