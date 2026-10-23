from django.urls import path

from . import views

app_name = "appointments"

urlpatterns = [
    path("", views.appointments_view, name="list"),
    path("create/", views.create_appointment_view, name="create"),
    path("<int:appointment_id>/status/", views.update_status_view, name="update_status"),
]
