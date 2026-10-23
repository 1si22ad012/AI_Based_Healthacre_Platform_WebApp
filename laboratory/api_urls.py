from django.urls import path

from . import api_views

urlpatterns = [
    path("requests/", api_views.LabRequestListCreateView.as_view(), name="requests"),
    path("reports/", api_views.LabReportListView.as_view(), name="reports"),
]
