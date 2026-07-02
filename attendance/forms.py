from django import forms
from .models import Course, Student


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ["code", "name"]
        widgets = {
            "code": forms.TextInput(attrs={"placeholder": "AI-101"}),
            "name": forms.TextInput(attrs={"placeholder": "Introduction to Artificial Intelligence"}),
        }


class StudentForm(forms.ModelForm):
    courses = forms.ModelMultipleChoiceField(
        queryset=Course.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Choose the teacher's classes in which this student is enrolled.",
    )

    class Meta:
        model = Student
        fields = ["student_id", "name", "email", "face_folder"]
        widgets = {"face_folder": forms.TextInput(attrs={"placeholder": "e.g. s001__rahul_kumar"})}

    def __init__(self, *args, teacher=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["courses"].queryset = Course.objects.filter(teacher=teacher) if teacher else Course.objects.none()
