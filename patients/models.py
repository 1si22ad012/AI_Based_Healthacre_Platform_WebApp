from django.conf import settings
from django.db import models

from accounts.models import PatientProfile, User


class Sensitivity(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"
    CRITICAL = "critical", "Critical"


class MedicalRecord(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name="medical_records")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_records")
    title = models.CharField(max_length=200)
    record_type = models.CharField(max_length=50, default="clinical_note")
    sensitivity = models.CharField(max_length=20, choices=Sensitivity.choices, default=Sensitivity.HIGH)
    encrypted_content = models.BinaryField()
    nonce = models.BinaryField()
    tag = models.BinaryField()
    algorithm = models.CharField(max_length=40, default="AES-256-GCM")
    key_version = models.CharField(max_length=40, default="dev-v1")
    content_hash = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        indexes = [models.Index(fields=["patient", "created_at"])]

    def __str__(self):
        return f"MedicalRecord({self.id}, {self.patient_id})"


class Diagnosis(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name="diagnoses")
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="diagnoses")
    title = models.CharField(max_length=200)
    encrypted_notes = models.BinaryField()
    nonce = models.BinaryField()
    tag = models.BinaryField()
    algorithm = models.CharField(max_length=40, default="AES-256-GCM")
    key_version = models.CharField(max_length=40, default="dev-v1")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["patient", "created_at"])]


class AccessGrant(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name="access_grants")
    granted_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="granted_patient_access")
    granted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="granted_access")
    reason = models.CharField(max_length=200, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
