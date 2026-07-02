from functools import wraps
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

TEACHERS_GROUP = "Teachers"


def has_teacher_access(user) -> bool:
    return bool(user.is_authenticated and (user.is_superuser or user.groups.filter(name=TEACHERS_GROUP).exists()))


def teacher_required(view_func):
    @login_required
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not has_teacher_access(request.user):
            return HttpResponseForbidden("Teacher access is required for this page.")
        return view_func(request, *args, **kwargs)
    return wrapped
