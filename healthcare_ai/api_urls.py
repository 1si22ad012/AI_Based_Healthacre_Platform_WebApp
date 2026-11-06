from django.urls import path

from . import api_views

urlpatterns = [
    path("symptom-assessment/", api_views.SymptomAssessmentApiView.as_view(), name="symptom-assessment"),
    path("chatbot/", api_views.ChatbotApiView.as_view(), name="chatbot"),
]