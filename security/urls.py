from django.urls import path

from . import views

app_name = "security"

urlpatterns = [
    path("encryption-activity/", views.encryption_activity_view, name="encryption_activity"),
    path("key-management/", views.key_management_view, name="key_management"),
    path("key-management/rotate/", views.rotate_key_view, name="rotate_key"),
    path("policy-demo/", views.policy_demo_view, name="policy_demo"),
    path("ai-monitoring/", views.ai_monitoring_view, name="ai_monitoring"),
    path("anomaly-history/", views.anomaly_history_view, name="anomaly_history"),
    path("anomalies/<int:detection_id>/", views.anomaly_detail_view, name="anomaly_detail"),
    path("incidents/", views.security_incidents_view, name="incidents"),
    path("model-information/", views.model_information_view, name="model_information"),
]