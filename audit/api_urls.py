from django.urls import path

from . import api_views

urlpatterns = [
    path("events/", api_views.AuditEventListView.as_view(), name="audit-events"),
]
