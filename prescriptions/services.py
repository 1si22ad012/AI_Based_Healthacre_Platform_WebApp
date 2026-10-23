import hashlib
import json
from decimal import Decimal

from django.conf import settings
from django.utils import timezone

from accounts.permissions import can_access_patient
from audit.services import create_audit_event
from security.services import ecc_sign, ecc_verify
from .models import Prescription, PrescriptionItem, PrescriptionStatus


def _signing_private_key_pem(user):
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives import serialization
    import hashlib

    seed = hashlib.sha256(f"healthcare-signing:{settings.SECRET_KEY}:{user.id}".encode()).digest()
    private_key = ec.derive_private_key(int.from_bytes(seed, "big"), ec.SECP256R1())
    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")


def _signing_public_key_pem(user):
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives import serialization
    import hashlib

    seed = hashlib.sha256(f"healthcare-signing:{settings.SECRET_KEY}:{user.id}".encode()).digest()
    private_key = ec.derive_private_key(int.from_bytes(seed, "big"), ec.SECP256R1())
    return private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")


def canonical_prescription_bytes(prescription, payload):
    data = {
        "id": prescription.id,
        "patient": prescription.patient.id,
        "doctor": prescription.doctor.id if prescription.doctor else None,
        "title": prescription.title,
        "payload": payload,
        "created_at": prescription.created_at.isoformat(),
    }
    return json.dumps(data, sort_keys=True, default=str).encode("utf-8")


def create_prescription(user, patient, title, payload, items=None, request=None, sign=True):
    if not (user.is_doctor() or user.is_administrator()):
        raise PermissionError("Only doctors can create prescriptions.")
    if not can_access_patient(user, patient):
        raise PermissionError("Not authorized for this patient.")

    from security.key_management import ensure_active_key
    from security.services import aes_encrypt

    key_size = 32
    base_version = settings.ENCRYPTION_KEY_VERSION
    key_version = f"{base_version}-aes256"
    ensure_active_key(key_version, key_size)
    plaintext = json.dumps(payload, default=str).encode("utf-8")
    ciphertext, nonce, tag, algorithm = aes_encrypt(plaintext, key_version, key_size)

    prescription = Prescription.objects.create(
        patient=patient,
        doctor=user,
        title=title,
        encrypted_payload=ciphertext,
        nonce=nonce,
        tag=tag,
        algorithm=algorithm,
        key_version=key_version,
        status=PrescriptionStatus.DRAFT,
    )
    for item in items or []:
        PrescriptionItem.objects.create(prescription=prescription, **item)

    if sign:
        payload_obj = payload
        data = canonical_prescription_bytes(prescription, payload_obj)
        signature = ecc_sign(_signing_private_key_pem(user), data)
        prescription.signature = signature
        prescription.signed_by = user
        prescription.signed_at = timezone.now()
        prescription.status = PrescriptionStatus.SIGNED
        prescription.save(update_fields=["signature", "signed_by", "signed_at", "status"])

    create_audit_event("prescription.create", actor=user, target_type="Prescription", target_id=prescription.id, request=request, result="success", details={"signed": sign})
    return prescription, payload


def decrypt_prescription(user, prescription):
    if not can_access_patient(user, prescription.patient) and prescription.doctor != user and not user.is_administrator():
        raise PermissionError("Not authorized.")
    from security.services import aes_decrypt, aes_key_size_from_algorithm

    key_size = aes_key_size_from_algorithm(prescription.algorithm)
    plaintext = aes_decrypt(prescription.encrypted_payload, prescription.nonce, prescription.tag, prescription.key_version, key_size)
    payload = json.loads(plaintext.decode("utf-8"))
    return payload


def verify_prescription_signature(prescription, payload):
    if not prescription.signature or not prescription.signed_by:
        return False
    data = canonical_prescription_bytes(prescription, payload)
    public_pem = _signing_public_key_pem(prescription.signed_by)
    return ecc_verify(public_pem, data, prescription.signature)
