from django.conf import settings
from django.db import models

from accounts.models import PatientProfile


class PrescriptionStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    ISSUED = "issued", "Issued"
    SIGNED = "signed", "Signed"
    CANCELLED = "cancelled", "Cancelled"


class Prescription(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name="prescriptions")
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="prescriptions")
    title = models.CharField(max_length=200)
    encrypted_payload = models.BinaryField()
    nonce = models.BinaryField()
    tag = models.BinaryField()
    algorithm = models.CharField(max_length=40, default="AES-256-GCM")
    key_version = models.CharField(max_length=40, default="dev-v1")
    status = models.CharField(max_length=20, choices=PrescriptionStatus.choices, default=PrescriptionStatus.DRAFT)
    signature = models.TextField(blank=True)
    signed_at = models.DateTimeField(null=True, blank=True)
    signed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="signed_prescriptions")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["patient", "created_at"])]


class PrescriptionItem(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name="items")
    medication_name = models.CharField(max_length=200)
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100)
    duration = models.CharField(max_length=100, blank=True)
    instructions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
