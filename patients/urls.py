from django.urls import path

from . import views

app_name = "patients"

urlpatterns = [
    path("records/", views.patient_records_view, name="records"),
    path("records/create/", views.create_record_view, name="create_record"),
    path("records/<int:record_id>/", views.view_record_view, name="view_record"),
    path("diagnoses/create/", views.create_diagnosis_view, name="create_diagnosis"),
]
