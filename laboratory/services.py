import hashlib
import json
from pathlib import Path

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.utils import timezone

from accounts.permissions import can_access_patient
from audit.services import create_audit_event, create_security_event
from security.models import EncryptedDocument
from security.services import aes_encrypt, aes_decrypt, aes_key_size_from_algorithm
from security.key_management import ensure_active_key
from .models import LabReport, LabTestRequest, LabTestStatus


ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".txt", ".csv"}


def create_lab_request(user, patient, test_type, priority="routine", notes="", technician=None, request=None):
    if not (user.is_doctor() or user.is_administrator()):
        raise PermissionError("Only doctors can request lab tests.")
    if not (user.is_administrator() or user.is_doctor()):
        if not can_access_patient(user, patient):
            raise PermissionError("Not authorized for this patient.")
    lab_request = LabTestRequest.objects.create(
        patient=patient, doctor=user, assigned_technician=technician,
        test_type=test_type, priority=priority, notes=notes,
    )
    create_audit_event("lab.request_create", actor=user, target_type="LabTestRequest", target_id=lab_request.id, request=request, result="success")
    return lab_request


def assign_technician(lab_request, technician, user):
    if not (user.is_doctor() or user.is_administrator()):
        raise PermissionError("Not authorized.")
    lab_request.assigned_technician = technician
    lab_request.status = LabTestStatus.IN_PROGRESS
    lab_request.save(update_fields=["assigned_technician", "status", "updated_at"])
    return lab_request


def upload_report(user, lab_request, uploaded_file: UploadedFile, result_text="", request=None):
    if not (user.is_lab_tech() or user.is_administrator()):
        raise PermissionError("Only laboratory technicians can upload reports.")
    if lab_request.assigned_technician and lab_request.assigned_technician != user and not user.is_administrator():
        raise PermissionError("This request is not assigned to you.")
    if uploaded_file.size > settings.MAX_UPLOAD_SIZE:
        raise ValueError("File too large.")
    ext = Path(uploaded_file.name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError("File type not allowed.")

    safe_name = f"report-{lab_request.id}-{timezone.now().timestamp()}{ext}"
    raw = uploaded_file.read()
    # Encrypt file bytes.
    key_size = 32
    base_version = settings.ENCRYPTION_KEY_VERSION
    key_version = f"{base_version}-aes256"
    ensure_active_key(key_version, key_size)
    ciphertext, nonce, tag, algorithm = aes_encrypt(raw, key_version, key_size, aad=lab_request.test_type.encode())

    doc = EncryptedDocument.objects.create(
        owner=lab_request.patient.user,
        original_filename=uploaded_file.name,
        safe_filename=safe_name,
        content_type=uploaded_file.content_type or "",
        file_size=uploaded_file.size,
        sha256=hashlib.sha256(raw).hexdigest(),
        ciphertext=ciphertext,
        nonce=nonce,
        tag=tag,
        algorithm=algorithm,
        key_version=key_version,
        related_type="LabTestRequest",
        related_id=lab_request.id,
        uploaded_by=user,
    )

    # Encrypt result text.
    result_ciphertext = b""
    result_nonce = b""
    result_tag = b""
    result_algorithm = algorithm
    if result_text:
        result_ciphertext, result_nonce, result_tag, result_algorithm = aes_encrypt(result_text.encode("utf-8"), key_version, key_size)

    report = LabReport.objects.create(
        request=lab_request,
        technician=user,
        encrypted_result=result_ciphertext or b"",
        nonce=result_nonce or b"",
        tag=result_tag or b"",
        algorithm=result_algorithm,
        key_version=key_version,
        status="submitted",
        completed_at=timezone.now(),
    )
    lab_request.status = LabTestStatus.COMPLETED
    lab_request.save(update_fields=["status", "updated_at"])
    create_audit_event("lab.report_upload", actor=user, target_type="LabReport", target_id=report.id, request=request, result="success", details={"document": doc.id, "request": lab_request.id})
    # Notify doctor/patient
    from notifications.models import Notification
    if lab_request.doctor:
        Notification.objects.create(recipient=lab_request.doctor, title="Lab report uploaded", message=f"Report for {lab_request.test_type} is available.", category="lab", url="/laboratory/reports/")
    if lab_request.patient and lab_request.patient.user:
        Notification.objects.create(recipient=lab_request.patient.user, title="Lab result available", message=f"Your {lab_request.test_type} result is available.", category="lab", url="/laboratory/reports/")
    return report, doc


def decrypt_report(user, report):
    # authorization: doctor who requested, assigned tech, patient, admin operational? admin no plaintext.
    lr = report.request
    patient = lr.patient
    if not (can_access_patient(user, patient) or lr.doctor == user or report.technician == user):
        raise PermissionError("Not authorized to view this report.")
    if not report.encrypted_result:
        return ""
    key_size = aes_key_size_from_algorithm(report.algorithm)
    return aes_decrypt(report.encrypted_result, report.nonce, report.tag, report.key_version, key_size).decode("utf-8")


def download_document(user, doc):
    if doc.owner != user and not (doc.uploaded_by == user):
        # doctors assigned? check related lab request
        related_allowed = False
        if doc.related_type == "LabTestRequest":
            from .models import LabTestRequest
            lr = LabTestRequest.objects.filter(id=doc.related_id).first()
            if lr and (lr.doctor == user or lr.assigned_technician == user or can_access_patient(user, lr.patient)):
                related_allowed = True
        if not related_allowed:
            raise PermissionError("Not authorized to download this document.")
    key_size = aes_key_size_from_algorithm(doc.algorithm)
    aad = b""
    if doc.related_type == "LabTestRequest":
        from .models import LabTestRequest
        lr = LabTestRequest.objects.filter(id=doc.related_id).first()
        if lr:
            aad = lr.test_type.encode()
    raw = aes_decrypt(doc.ciphertext, doc.nonce, doc.tag, doc.key_version, key_size, aad=aad)
    # integrity check
    if hashlib.sha256(raw).hexdigest() != doc.sha256:
        raise ValueError("Integrity verification failed.")
    return raw, doc


def reject_report(user, report):
    if not (user.is_lab_tech() or user.is_administrator()):
        raise PermissionError("Not authorized.")
    report.status = "rejected"
    report.save(update_fields=["status", "updated_at"])
    report.request.status = LabTestStatus.REJECTED
    report.request.save(update_fields=["status", "updated_at"])
    return report
