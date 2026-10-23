from rest_framework import serializers

from .models import AuditEvent, SecurityEvent, AnomalyAlert


class AuditEventSerializer(serializers.ModelSerializer):
    actor_email = serializers.CharField(source="actor.email", read_only=True)

    class Meta:
        model = AuditEvent
        fields = ["id", "actor", "actor_email", "action", "target_type", "target_id", "result", "severity", "ip_address", "correlation_id", "details", "prev_hash", "entry_hash", "created_at"]


class SecurityEventSerializer(serializers.ModelSerializer):
    actor_email = serializers.CharField(source="actor.email", read_only=True)

    class Meta:
        model = SecurityEvent
        fields = ["id", "actor", "actor_email", "event_type", "severity", "ip_address", "user_agent", "metadata", "risk_score", "created_at"]


class AnomalyAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnomalyAlert
        fields = ["id", "security_event", "detector", "score", "threshold", "status", "resolution_notes", "created_at", "resolved_at"]
