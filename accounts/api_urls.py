from django.urls import path

from . import api_views

urlpatterns = [
    path("me/", api_views.MeView.as_view(), name="me"),
    path("register/", api_views.RegisterView.as_view(), name="register"),
    path("users/", api_views.UserListView.as_view(), name="users"),
    path("users/<int:pk>/", api_views.UserDetailView.as_view(), name="user-detail"),
]
