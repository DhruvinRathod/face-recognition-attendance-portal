from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand, CommandError
from attendance.models import Course, Enrollment, Student
from attendance.permissions import TEACHERS_GROUP


class Command(BaseCommand):
    help = "Create a teacher account plus a small demo course and students for local testing."

    def add_arguments(self, parser):
        parser.add_argument("--username", default="teacher")
        parser.add_argument("--password", default="TeacherDemo123!")

    def handle(self, *args, **options):
        username = options["username"]
        password = options["password"]
        if len(password) < 8:
            raise CommandError("Use a password with at least eight characters.")

        group, _ = Group.objects.get_or_create(name=TEACHERS_GROUP)
        user, created = User.objects.get_or_create(username=username, defaults={"first_name": "Demo", "last_name": "Teacher"})
        user.set_password(password)
        user.save()
        user.groups.add(group)

        course, _ = Course.objects.get_or_create(
            code="AI-101",
            defaults={"name": "Introduction to Artificial Intelligence", "teacher": user},
        )
        if course.teacher_id != user.id:
            self.stdout.write(self.style.WARNING(f"AI-101 already belongs to {course.teacher.username}; no course owner was changed."))

        for student_id, name in [("S001", "Demo Student One"), ("S002", "Demo Student Two")]:
            student, _ = Student.objects.get_or_create(student_id=student_id, defaults={"name": name})
            if course.teacher_id == user.id:
                Enrollment.objects.get_or_create(course=course, student=student)

        action = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{action} teacher login: {username}"))
        self.stdout.write("Demo course: AI-101. Demo students: S001 and S002.")
        self.stdout.write("For local demo only: change the password before any real use.")
