from django.urls import path

from . import api_views

urlpatterns = [
    path("records/", api_views.MedicalRecordListView.as_view(), name="records"),
    path("records/create/", api_views.CreateEncryptedRecordView.as_view(), name="create-record"),
]
