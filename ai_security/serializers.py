from rest_framework import serializers

from audit.models import AnomalyAlert, SecurityEvent


class SecurityEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = SecurityEvent
        fields = ["id", "actor", "event_type", "severity", "ip_address", "metadata", "risk_score", "created_at"]
        read_only_fields = fields


class AnomalyAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnomalyAlert
        fields = ["id", "security_event", "detector", "score", "threshold", "status", "resolution_notes", "created_at", "resolved_at"]
        read_only_fields = fields
