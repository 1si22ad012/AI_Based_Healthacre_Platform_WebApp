from django.conf import settings
from django.db import models

from accounts.models import PatientProfile


class AppointmentStatus(models.TextChoices):
    REQUESTED = "requested", "Requested"
    SCHEDULED = "scheduled", "Scheduled"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"


class Appointment(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name="appointments")
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="appointments")
    scheduled_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=AppointmentStatus.choices, default=AppointmentStatus.REQUESTED)
    reason = models.CharField(max_length=255, blank=True)
    encrypted_notes = models.BinaryField(null=True, blank=True)
    nonce = models.BinaryField(null=True, blank=True)
    tag = models.BinaryField(null=True, blank=True)
    algorithm = models.CharField(max_length=40, blank=True)
    key_version = models.CharField(max_length=40, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_appointments")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["patient", "scheduled_at"]), models.Index(fields=["doctor", "scheduled_at"])]
