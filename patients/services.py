import hashlib
import json
import time
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from accounts.models import Role
from accounts.permissions import can_access_patient
from ai_security.services import detect_anomaly, select_policy
from audit.services import create_audit_event, create_security_event
from security.key_management import ensure_active_key
from security.models import EncryptionOperation, KeyMetadata
from security.services import aes_decrypt, aes_encrypt, aes_key_size_from_algorithm

from .models import Diagnosis, MedicalRecord, Sensitivity


def _recent_security_events(user):
    from audit.models import SecurityEvent

    # Count only security events that indicate suspicious activity. Normal
    # authentication and logout events must not inflate the risk score, and
    # policy-block events must not create a feedback loop.
    since = timezone.now() - timedelta(hours=1)
    suspicious_types = {"login_failure", "access_denied", "anomaly", "decryption_failure"}
    events = SecurityEvent.objects.filter(actor=user, created_at__gte=since, event_type__in=suspicious_types)
    return events.exclude(event_type="access_denied", metadata__reason="elevated_risk_policy").count()


def _risk_level(anomaly_result):
    if anomaly_result.get("is_anomaly"):
        return "high"
    return "low"


def encrypt_medical_record(user, patient, title, content, sensitivity="high", request=None):
    if not can_access_patient(user, patient):
        raise PermissionError("You are not authorized to create records for this patient.")

    anomaly_context = {
        "failed_logins": user.failed_login_count,
        "login_frequency": _recent_security_events(user),
        "unusual_hour": 1 if timezone.now().hour < 6 or timezone.now().hour > 22 else 0,
        "denied_requests": 0,
        "upload_size_kb": len(content.encode()) / 1024.0,
        "record_access_count": MedicalRecord.objects.filter(patient=patient).count(),
        "cpu_utilization": 0.0,
        "encryption_failures": EncryptionOperation.objects.filter(user=user, success=False).count(),
        "invalid_tags": 0,
        "suspicious_params": 0,
    }
    anomaly_result = detect_anomaly(anomaly_context)
    context = {
        "sensitivity": sensitivity,
        "role": user.role,
        "file_size_kb": len(content.encode()) / 1024.0,
        "cpu_utilization": 0.0,
        "network_latency": 0.0,
        "recent_security_events": _recent_security_events(user),
        "anomaly_score": anomaly_result.get("score", 0.0),
        "access_frequency": MedicalRecord.objects.filter(patient=patient).count(),
        "risk_level": _risk_level(anomaly_result),
    }
    policy = select_policy(context)
    if not policy.get("allowed", False):
        create_security_event(
            "access_denied",
            actor=user,
            request=request,
            metadata={
                "reason": "elevated_risk_policy",
                "feature_summary": {
                    "sensitivity": sensitivity,
                    "recent_security_events": context["recent_security_events"],
                    "anomaly_score": context["anomaly_score"],
                    "anomaly_detected": anomaly_result.get("is_anomaly", False),
                    "detector_summary": anomaly_result.get("detectors", {}),
                    "model_recommendation": policy.get("model_recommendation"),
                    "policy": policy.get("policy"),
                },
            },
            severity="high",
            risk_score=max(0.9, float(context.get("anomaly_score", 0.0) or 0.0)),
        )
        create_audit_event(
            "record.create_denied",
            actor=user,
            target_type="Patient",
            target_id=patient.id,
            request=request,
            result="denied",
            severity="high",
            details={"reason": "elevated_risk_policy", "policy": policy.get("policy"), "anomaly_score": context["anomaly_score"]},
        )
        raise PermissionError("Operation blocked by security policy.")

    key_size = policy["key_size"]
    base_version = settings.ENCRYPTION_KEY_VERSION
    key_version = f"{base_version}-aes{key_size * 8}"
    ensure_active_key(key_version, key_size)

    start = time.perf_counter()
    try:
        ciphertext, nonce, tag, algorithm = aes_encrypt(content.encode("utf-8"), key_version, key_size)
    except Exception as exc:
        EncryptionOperation.objects.create(
            user=user, operation="encrypt", policy=policy["policy"], algorithm=policy["algorithm"],
            key_version=key_version, sensitivity=sensitivity, data_size=len(content.encode()),
            duration_ms=(time.perf_counter() - start) * 1000.0, success=False, error_code=str(exc),
            model_version=policy.get("model_version", ""), fallback_used=policy.get("fallback_used", False),
            correlation_id="",
        )
        raise

    with transaction.atomic():
        record = MedicalRecord.objects.create(
            patient=patient,
            created_by=user,
            title=title,
            record_type="clinical_note",
            sensitivity=sensitivity,
            encrypted_content=ciphertext,
            nonce=nonce,
            tag=tag,
            algorithm=algorithm,
            key_version=key_version,
            content_hash=hashlib.sha256(content.encode()).hexdigest(),
        )
        EncryptionOperation.objects.create(
            user=user, operation="encrypt", policy=policy["policy"], algorithm=algorithm,
            key_version=key_version, sensitivity=sensitivity, data_size=len(content.encode()),
            duration_ms=(time.perf_counter() - start) * 1000.0, success=True,
            model_version=policy.get("model_version", ""), fallback_used=policy.get("fallback_used", False),
        )
        create_audit_event(
            "record.create", actor=user, target_type="MedicalRecord", target_id=record.id,
            request=request, result="success", details={"policy": policy["policy"], "algorithm": algorithm, "key_version": key_version, "patient": patient.id},
        )
    return record, policy


def decrypt_medical_record(user, record, request=None):
    if not can_access_patient(user, record.patient):
        create_security_event("access_denied", actor=user, request=request, metadata={"record_id": record.id}, severity="high", risk_score=0.7)
        create_audit_event("record.access_denied", actor=user, target_type="MedicalRecord", target_id=record.id, request=request, result="denied")
        raise PermissionError("You are not authorized to access this record.")

    key_size = aes_key_size_from_algorithm(record.algorithm)
    start = time.perf_counter()
    try:
        plaintext = aes_decrypt(record.encrypted_content, record.nonce, record.tag, record.key_version, key_size)
    except Exception as exc:
        EncryptionOperation.objects.create(
            user=user, operation="decrypt", policy="n/a", algorithm=record.algorithm,
            key_version=record.key_version, sensitivity=record.sensitivity, data_size=len(record.encrypted_content),
            duration_ms=(time.perf_counter() - start) * 1000.0, success=False, error_code=str(exc),
        )
        create_security_event("decryption_failure", actor=user, request=request, metadata={"record_id": record.id}, severity="high", risk_score=0.8)
        raise
    EncryptionOperation.objects.create(
        user=user, operation="decrypt", policy="n/a", algorithm=record.algorithm,
        key_version=record.key_version, sensitivity=record.sensitivity, data_size=len(record.encrypted_content),
        duration_ms=(time.perf_counter() - start) * 1000.0, success=True,
    )
    create_audit_event(
        "record.decrypt", actor=user, target_type="MedicalRecord", target_id=record.id,
        request=request, result="success", details={"patient": record.patient.id},
    )
    return plaintext.decode("utf-8"), record


def create_diagnosis(user, patient, title, notes, request=None):
    if not (user.is_doctor() or user.is_administrator()):
        raise PermissionError("Only doctors can create diagnoses.")
    if not can_access_patient(user, patient):
        raise PermissionError("Not authorized for this patient.")
    sensitivity = "high"
    # Reuse encryption logic manually.
    from .models import Diagnosis

    key_size = 32
    base_version = settings.ENCRYPTION_KEY_VERSION
    key_version = f"{base_version}-aes256"
    ensure_active_key(key_version, key_size)
    ciphertext, nonce, tag, algorithm = aes_encrypt(notes.encode("utf-8"), key_version, key_size)
    with transaction.atomic():
        diagnosis = Diagnosis.objects.create(
            patient=patient, doctor=user, title=title,
            encrypted_notes=ciphertext, nonce=nonce, tag=tag, algorithm=algorithm, key_version=key_version,
        )
        create_audit_event("diagnosis.create", actor=user, target_type="Diagnosis", target_id=diagnosis.id, request=request, result="success")
    return diagnosis
