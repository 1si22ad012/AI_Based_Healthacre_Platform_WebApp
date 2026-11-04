from django.urls import path

from . import views

app_name = "healthcare_ai"

urlpatterns = [
    path("doctor-search/", views.doctor_search_view, name="doctor_search"),
    path("symptom-assessment/", views.symptom_assessment_view, name="symptom_assessment"),
    path("chatbot/", views.chatbot_view, name="chatbot"),
    path("security-incidents/", views.security_incidents_view, name="security_incidents"),
    path("face-verification/", views.face_verification_view, name="face_verification"),
    path("risk-analysis/", views.risk_analysis_view, name="risk_analysis"),
    path("incident-summary/<int:incident_id>/", views.incident_summary_view, name="incident_summary"),
]
