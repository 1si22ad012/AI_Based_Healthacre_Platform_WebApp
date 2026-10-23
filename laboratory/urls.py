from django.urls import path

from . import views

app_name = "laboratory"

urlpatterns = [
    path("requests/", views.lab_requests_view, name="requests"),
    path("requests/create/", views.create_request_view, name="create_request"),
    path("reports/", views.reports_view, name="reports"),
    path("reports/upload/", views.upload_report_view, name="upload_report"),
    path("reports/<int:report_id>/reject/", views.reject_report_view, name="reject_report"),
    path("documents/<int:document_id>/download/", views.download_report_view, name="download_document"),
]
