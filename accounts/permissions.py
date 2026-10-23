from rest_framework import permissions

from .models import Role, User


def role_of(user):
    if not user or not user.is_authenticated:
        return None
    if user.is_superuser:
        return Role.ADMIN
    return user.role


def is_admin(user):
    return bool(user and user.is_authenticated and (user.is_superuser or user.role == Role.ADMIN))


def is_doctor(user):
    return bool(user and user.is_authenticated and user.role == Role.DOCTOR)


def is_patient(user):
    return bool(user and user.is_authenticated and user.role == Role.PATIENT)


def is_lab_tech(user):
    return bool(user and user.is_authenticated and user.role == Role.LAB_TECH)


def can_access_patient(user, patient_profile):
    if not user or not user.is_authenticated:
        return False
    if is_admin(user):
        # Administrators retain operational access but not automatic clinical plaintext access.
        return False
    if is_patient(user):
        return getattr(user, "patient_profile", None) == patient_profile
    if is_doctor(user):
        # Access is granted through AccessGrant or assigned appointments/records.
        from patients.models import AccessGrant
        if AccessGrant.objects.filter(patient=patient_profile, granted_to=user, is_active=True).exists():
            return True
        # Doctors who have an appointment or created a record for the patient are authorized.
        from appointments.models import Appointment
        if Appointment.objects.filter(patient=patient_profile, doctor=user).exists():
            return True
        from patients.models import MedicalRecord, Diagnosis
        if MedicalRecord.objects.filter(patient=patient_profile, created_by=user).exists():
            return True
        if Diagnosis.objects.filter(patient=patient_profile, doctor=user).exists():
            return True
        from prescriptions.models import Prescription
        if Prescription.objects.filter(patient=patient_profile, doctor=user).exists():
            return True
        from laboratory.models import LabTestRequest
        if LabTestRequest.objects.filter(patient=patient_profile, doctor=user).exists():
            return True
        return False
    if is_lab_tech(user):
        from laboratory.models import LabTestRequest
        return LabTestRequest.objects.filter(patient=patient_profile, assigned_technician=user).exists()
    return False


class IsPatient(permissions.BasePermission):
    def has_permission(self, request, view):
        return is_patient(request.user)


class IsDoctor(permissions.BasePermission):
    def has_permission(self, request, view):
        return is_doctor(request.user)


class IsLabTech(permissions.BasePermission):
    def has_permission(self, request, view):
        return is_lab_tech(request.user)


class IsAdministrator(permissions.BasePermission):
    def has_permission(self, request, view):
        return is_admin(request.user)


class IsOwnerOrAuthorized(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if is_admin(user):
            return True
        if hasattr(obj, "user") and obj.user == user:
            return True
        if hasattr(obj, "patient") and hasattr(obj.patient, "user"):
            return can_access_patient(user, obj.patient)
        if hasattr(obj, "recipient") and obj.recipient == user:
            return True
        return False
