from django.urls import path

from . import api_views

urlpatterns = [
    path("appointments/", api_views.AppointmentListCreateView.as_view(), name="appointments"),
]
