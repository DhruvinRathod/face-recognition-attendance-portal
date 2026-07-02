from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from attendance.views import logout_view

urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", logout_view, name="logout"),
    path("", include("attendance.urls")),
]
