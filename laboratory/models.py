from django.conf import settings
from django.db import models

from accounts.models import PatientProfile, User


class LabTestStatus(models.TextChoices):
    REQUESTED = "requested", "Requested"
    IN_PROGRESS = "in_progress", "In Progress"
    COMPLETED = "completed", "Completed"
    REJECTED = "rejected", "Rejected"


class LabTestRequest(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name="lab_requests")
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="lab_requests")
    assigned_technician = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_lab_requests")
    test_type = models.CharField(max_length=100)
    priority = models.CharField(max_length=20, default="routine")
    status = models.CharField(max_length=20, choices=LabTestStatus.choices, default=LabTestStatus.REQUESTED)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["patient", "status"]), models.Index(fields=["assigned_technician", "status"])]


class LabReport(models.Model):
    request = models.ForeignKey(LabTestRequest, on_delete=models.CASCADE, related_name="reports")
    technician = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="lab_reports")
    encrypted_result = models.BinaryField()
    nonce = models.BinaryField()
    tag = models.BinaryField()
    algorithm = models.CharField(max_length=40, default="AES-256-GCM")
    key_version = models.CharField(max_length=40, default="dev-v1")
    status = models.CharField(max_length=20, default="submitted")
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
