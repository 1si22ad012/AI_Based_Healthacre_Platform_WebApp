from django.conf import settings
from django.db import models


class KeyStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    ROTATED = "rotated", "Rotated"
    REVOKED = "revoked", "Revoked"
    COMPROMISED = "compromised", "Compromised"


class KeyMetadata(models.Model):
    key_id = models.CharField(max_length=64, unique=True)
    version = models.CharField(max_length=40, unique=True)
    algorithm = models.CharField(max_length=40, default="AES-256-GCM")
    status = models.CharField(max_length=20, choices=KeyStatus.choices, default=KeyStatus.ACTIVE)
    fingerprint = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    rotated_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.version} ({self.status})"


class EncryptedDocument(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="encrypted_documents")
    original_filename = models.CharField(max_length=255)
    safe_filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100, blank=True)
    file_size = models.PositiveIntegerField(default=0)
    sha256 = models.CharField(max_length=64)
    ciphertext = models.BinaryField()
    nonce = models.BinaryField()
    tag = models.BinaryField()
    algorithm = models.CharField(max_length=40, default="AES-256-GCM")
    key_version = models.CharField(max_length=40, default="dev-v1")
    related_type = models.CharField(max_length=80, blank=True)
    related_id = models.PositiveBigIntegerField(null=True, blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="uploaded_encrypted_documents")
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        indexes = [models.Index(fields=["owner", "created_at"])]


class EncryptionOperation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="encryption_operations")
    operation = models.CharField(max_length=30)
    policy = models.CharField(max_length=40)
    algorithm = models.CharField(max_length=40)
    key_version = models.CharField(max_length=40)
    sensitivity = models.CharField(max_length=20, blank=True)
    data_size = models.PositiveIntegerField(default=0)
    duration_ms = models.FloatField(default=0)
    success = models.BooleanField(default=True)
    error_code = models.CharField(max_length=80, blank=True)
    model_version = models.CharField(max_length=40, blank=True)
    fallback_used = models.BooleanField(default=False)
    correlation_id = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["user", "created_at"]), models.Index(fields=["success", "created_at"])]


class SecurityPolicySetting(models.Model):
    key = models.CharField(max_length=80, unique=True)
    value = models.JSONField(default=dict)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    updated_at = models.DateTimeField(auto_now=True)
