from django.urls import path

from . import views

app_name = "ai"

urlpatterns = [
    path("monitoring/", views.security_monitoring_view, name="monitoring"),
    path("anomaly-alerts/", views.anomaly_alerts_view, name="anomaly_alerts"),
    path("detect-demo/", views.detect_demo_view, name="detect_demo"),
]
