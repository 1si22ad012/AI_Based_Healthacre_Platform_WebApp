from django.conf import settings
from django.utils import timezone

from accounts.permissions import can_access_patient
from audit.services import create_audit_event
from security.key_management import ensure_active_key
from security.services import aes_encrypt, aes_decrypt, aes_key_size_from_algorithm
from .models import Appointment, AppointmentStatus


def create_appointment(user, patient, scheduled_at, reason="", notes="", doctor=None, request=None):
    if not can_access_patient(user, patient) and not (user.is_doctor() or user.is_administrator()):
        raise PermissionError("Not authorized to create this appointment.")
    appointment = Appointment(
        patient=patient,
        doctor=doctor or (user if user.is_doctor() else None),
        scheduled_at=scheduled_at,
        status=AppointmentStatus.REQUESTED,
        reason=reason,
        created_by=user,
    )
    if notes:
        key_size = 32
        key_version = f"{settings.ENCRYPTION_KEY_VERSION}-aes256"
        ensure_active_key(key_version, key_size)
        ciphertext, nonce, tag, algorithm = aes_encrypt(notes.encode("utf-8"), key_version, key_size)
        appointment.encrypted_notes = ciphertext
        appointment.nonce = nonce
        appointment.tag = tag
        appointment.algorithm = algorithm
        appointment.key_version = key_version
    appointment.save()
    create_audit_event("appointment.create", actor=user, target_type="Appointment", target_id=appointment.id, request=request, result="success")
    return appointment


def decrypt_appointment_notes(user, appointment):
    if not appointment.encrypted_notes:
        return ""
    if not can_access_patient(user, appointment.patient) and appointment.doctor != user and not user.is_administrator():
        raise PermissionError("Not authorized.")
    key_size = aes_key_size_from_algorithm(appointment.algorithm or "AES-256-GCM")
    return aes_decrypt(appointment.encrypted_notes, appointment.nonce, appointment.tag, appointment.key_version, key_size).decode("utf-8")
