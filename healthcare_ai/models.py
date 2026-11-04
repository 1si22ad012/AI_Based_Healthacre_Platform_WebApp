from django.conf import settings
from django.db import models


class SymptomAssessment(models.Model):
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="symptom_assessments")
    symptoms = models.TextField()
    predicted_specialties = models.JSONField(default=list)
    emergency = models.BooleanField(default=False)
    explanation = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class AIConversation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ai_conversations")
    message = models.TextField()
    response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class SecurityIncident(models.Model):
    STATUS_CHOICES = [
        ("new", "New"),
        ("under_investigation", "Under Investigation"),
        ("acknowledged", "Acknowledged"),
        ("resolved", "Resolved"),
        ("false_positive", "False Positive"),
    ]
    title = models.CharField(max_length=200)
    severity = models.CharField(max_length=20, default="medium")
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="new")
    summary = models.TextField(blank=True)
    related_events = models.JSONField(default=list)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_incidents")
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    history = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]


class LoginAudit(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="login_audits")
    login_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    risk_score = models.FloatField(default=0.0)
    risk_level = models.CharField(max_length=20, default="low")
    email_sent = models.BooleanField(default=False)
    reported_unfamiliar = models.BooleanField(default=False)

    class Meta:
        ordering = ["-login_at"]


class FaceVerificationRecord(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="face_verifications")
    enrolled = models.BooleanField(default=False)
    consent_given = models.BooleanField(default=False)
    template_hash = models.CharField(max_length=128, blank=True)
    enrolled_at = models.DateTimeField(null=True, blank=True)
    last_verified_at = models.DateTimeField(null=True, blank=True)
    verification_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-enrolled_at"]