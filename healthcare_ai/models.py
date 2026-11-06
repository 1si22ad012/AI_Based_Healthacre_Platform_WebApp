from django.conf import settings
from django.db import models


class SymptomAssessment(models.Model):
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="symptom_assessments")
    symptoms = models.TextField()
    duration = models.CharField(max_length=100, blank=True)
    severity = models.CharField(max_length=40, blank=True)
    onset = models.CharField(max_length=100, blank=True)
    frequency = models.CharField(max_length=100, blank=True)
    trend = models.CharField(max_length=40, blank=True)
    medical_history = models.TextField(blank=True)
    medications = models.TextField(blank=True)
    allergies = models.TextField(blank=True)
    age_range = models.CharField(max_length=40, blank=True)
    predicted_specialties = models.JSONField(default=list)
    emergency = models.BooleanField(default=False)
    recommended_urgency = models.CharField(max_length=40, default="routine")
    missing_info = models.JSONField(default=list, blank=True)
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


class MedicalKnowledgeChunk(models.Model):
    source_title = models.CharField(max_length=255)
    source_url = models.URLField(max_length=500, blank=True)
    source_type = models.CharField(max_length=80, default="public_health")
    chunk_text = models.TextField()
    keywords = models.JSONField(default=list, blank=True)
    version = models.CharField(max_length=40, default="v1")
    retrieved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["source_title", "id"]
        indexes = [models.Index(fields=["source_title"])]

    def __str__(self):
        return f"{self.source_title} chunk {self.id}"


class ChatConversation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chat_conversations")
    title = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"ChatConversation({self.id}, {self.user.email})"


class ChatMessage(models.Model):
    ROLE_CHOICES = [("user", "User"), ("assistant", "Assistant"), ("system", "System")]
    conversation = models.ForeignKey(ChatConversation, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    sources = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"ChatMessage({self.id}, {self.role})"


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