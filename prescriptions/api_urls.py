from django.urls import path

from . import api_views

urlpatterns = [
    path("prescriptions/", api_views.PrescriptionListView.as_view(), name="prescriptions"),
]
