from django.conf import settings
from django.db import models


class Severity(models.TextChoices):
    INFO = "info", "Info"
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"
    CRITICAL = "critical", "Critical"


class SecurityEventType(models.TextChoices):
    LOGIN_SUCCESS = "login_success", "Login Success"
    LOGIN_FAILURE = "login_failure", "Login Failure"
    LOGOUT = "logout", "Logout"
    ACCESS_DENIED = "access_denied", "Access Denied"
    RECORD_ACCESS = "record_access", "Record Access"
    RECORD_CREATE = "record_create", "Record Create"
    ENCRYPTION = "encryption", "Encryption"
    DECRYPTION = "decryption", "Decryption"
    UPLOAD = "upload", "Upload"
    DOWNLOAD = "download", "Download"
    KEY_ROTATION = "key_rotation", "Key Rotation"
    ANOMALY = "anomaly", "Anomaly"
    POLICY_CHANGE = "policy_change", "Policy Change"
    ADMIN_ACTION = "admin_action", "Admin Action"


class SecurityEvent(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="security_events")
    event_type = models.CharField(max_length=40, choices=SecurityEventType.choices)
    severity = models.CharField(max_length=20, choices=Severity.choices, default=Severity.INFO)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    risk_score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["event_type", "created_at"]), models.Index(fields=["actor", "created_at"])]


class AnomalyAlert(models.Model):
    security_event = models.ForeignKey(SecurityEvent, on_delete=models.CASCADE, related_name="anomaly_alerts")
    detector = models.CharField(max_length=40)
    score = models.FloatField()
    threshold = models.FloatField()
    status = models.CharField(max_length=20, default="open")
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_alerts")
    resolution_notes = models.TextField(blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["status", "created_at"])]


class AnomalyDetection(models.Model):
    STATUS_OPEN = "open"
    STATUS_REVIEWED = "reviewed"
    STATUS_CLOSED = "closed"

    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="anomaly_detections")
    user_role = models.CharField(max_length=20, blank=True)
    event_type = models.CharField(max_length=40, default="anomaly")
    detector = models.CharField(max_length=40, default="hybrid")
    model_version = models.CharField(max_length=40, blank=True)
    input_features = models.JSONField(default=dict, blank=True)
    isolation_forest_prediction = models.CharField(max_length=20, blank=True)
    isolation_forest_score = models.FloatField(default=0.0)
    one_class_svm_prediction = models.CharField(max_length=20, blank=True)
    one_class_svm_score = models.FloatField(default=0.0)
    random_forest_prediction = models.CharField(max_length=20, blank=True)
    random_forest_score = models.FloatField(default=0.0)
    combined_score = models.FloatField(default=0.0)
    threshold = models.FloatField(default=0.5)
    is_anomaly = models.BooleanField(default=False)
    risk_score = models.FloatField(default=0.0)
    risk_level = models.CharField(max_length=20, default="low")
    action_taken = models.CharField(max_length=80, blank=True)
    reasons = models.JSONField(default=list, blank=True)
    detection_status = models.CharField(max_length=20, default="open")
    security_event = models.ForeignKey("SecurityEvent", on_delete=models.SET_NULL, null=True, blank=True, related_name="anomaly_detections")
    anomaly_alert = models.ForeignKey("AnomalyAlert", on_delete=models.SET_NULL, null=True, blank=True, related_name="detections")
    security_incident = models.ForeignKey("healthcare_ai.SecurityIncident", on_delete=models.SET_NULL, null=True, blank=True, related_name="anomaly_detections")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["is_anomaly", "created_at"]), models.Index(fields=["actor", "created_at"])]

    def __str__(self):
        return f"AnomalyDetection({self.id}, anomaly={self.is_anomaly})"


class AuditEvent(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_events")
    action = models.CharField(max_length=80)
    target_type = models.CharField(max_length=80, blank=True)
    target_id = models.CharField(max_length=80, blank=True)
    result = models.CharField(max_length=20, default="success")
    severity = models.CharField(max_length=20, choices=Severity.choices, default=Severity.INFO)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    correlation_id = models.CharField(max_length=64, blank=True)
    details = models.JSONField(default=dict, blank=True)
    prev_hash = models.CharField(max_length=64, blank=True)
    entry_hash = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["action", "created_at"]), models.Index(fields=["actor", "created_at"])]
