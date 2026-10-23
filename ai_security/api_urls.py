from django.urls import path

from . import api_views

urlpatterns = [
    path("events/", api_views.SecurityEventListView.as_view(), name="events"),
    path("alerts/", api_views.AnomalyAlertListView.as_view(), name="alerts"),
    path("detect/", api_views.DetectAnomalyView.as_view(), name="detect"),
]
