from django.conf import settings
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from attendance.views import demo_login, logout_view

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="registration/login.html",
            extra_context={"demo_mode": settings.DEMO_MODE},
        ),
        name="login",
    ),
    path("demo-login/", demo_login, name="demo_login"),
    path("logout/", logout_view, name="logout"),
    path("", include("attendance.urls")),
]
