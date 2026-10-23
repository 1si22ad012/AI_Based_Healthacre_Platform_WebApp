from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("", views.dashboard_router, name="dashboard"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register_view, name="register"),
    path("password-change/", views.password_change_view, name="password_change"),
    path("profile/", views.profile_view, name="profile"),
    path("users/", views.user_management_view, name="user_management"),
    path("users/<int:user_id>/toggle/", views.toggle_user_view, name="toggle_user"),
]
