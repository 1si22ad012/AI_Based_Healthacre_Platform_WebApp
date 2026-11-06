from rest_framework import serializers

from .models import SymptomAssessment, ChatConversation, ChatMessage


class SymptomAssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SymptomAssessment
        fields = ["id", "symptoms", "duration", "severity", "predicted_specialties", "emergency", "recommended_urgency", "explanation", "created_at"]


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ["id", "role", "content", "sources", "created_at"]