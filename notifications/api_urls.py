from django.urls import path

from . import api_views

urlpatterns = [
    path("notifications/", api_views.NotificationListView.as_view(), name="notifications"),
]
