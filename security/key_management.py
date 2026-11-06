import base64
import hashlib
import secrets
from datetime import timedelta

from django.utils import timezone

from .models import KeyActivity, KeyMetadata, KeyStatus
from .services import derive_key


def key_fingerprint(version: str, key_size: int = 32) -> str:
    return hashlib.sha256(derive_key(version, key_size)).hexdigest()


def _backfill_key_metadata(obj):
    if obj.activated_at is None:
        obj.activated_at = obj.created_at or timezone.now()
    if obj.usage_count is None:
        obj.usage_count = 0
    if not obj.rotation_history:
        obj.rotation_history = []
    obj.save(update_fields=["activated_at", "usage_count", "rotation_history"])


def ensure_active_key(version: str = None, key_size: int = 32, actor=None) -> KeyMetadata:
    from django.conf import settings

    version = version or getattr(settings, "ENCRYPTION_KEY_VERSION", "dev-v1")
    if not version:
        version = "dev-v1"
    obj, created = KeyMetadata.objects.get_or_create(
        version=version,
        defaults={
            "key_id": f"key-{version}",
            "algorithm": f"AES-{key_size * 8}-GCM",
            "key_type": "data_encryption",
            "status": KeyStatus.ACTIVE,
            "fingerprint": key_fingerprint(version, key_size),
            "activated_at": timezone.now(),
            "usage_count": 0,
            "rotation_history": [],
            "notes": "Development key metadata. Production must use a secret manager.",
        },
    )
    if created:
        KeyActivity.objects.create(
            key_version=obj.version,
            action="generated",
            actor=actor,
            status="success",
            message=f"Key {obj.version} generated and activated.",
            metadata={"algorithm": obj.algorithm, "key_id": obj.key_id},
        )
        KeyActivity.objects.create(
            key_version=obj.version,
            action="activated",
            actor=actor,
            status="success",
            message=f"Key {obj.version} activated.",
        )
        return obj
    _backfill_key_metadata(obj)
    if obj.status != KeyStatus.ACTIVE:
        obj.status = KeyStatus.ACTIVE
        obj.activated_at = obj.activated_at or timezone.now()
        obj.save(update_fields=["status", "activated_at"])
        KeyActivity.objects.create(
            key_version=obj.version,
            action="activated",
            actor=actor,
            status="success",
            message=f"Key {obj.version} reactivated.",
        )
    return obj


def rotate_key(old_version: str, key_size: int = 32, actor=None) -> KeyMetadata:
    from django.utils import timezone as tz

    new_version = f"v{int(tz.now().timestamp())}"
    old = KeyMetadata.objects.filter(version=old_version).first()
    if old:
        old.status = KeyStatus.ROTATED
        old.rotated_at = tz.now()
        old.rotation_history = list(old.rotation_history or []) + [
            {"action": "rotated", "at": tz.now().isoformat(), "successor": new_version}
        ]
        old.save(update_fields=["status", "rotated_at", "rotation_history"])
        KeyActivity.objects.create(
            key_version=old.version,
            action="rotated",
            actor=actor,
            status="success",
            message=f"Key {old.version} rotated to {new_version}.",
            metadata={"successor": new_version},
        )
    new = KeyMetadata.objects.create(
        key_id=f"key-{new_version}",
        version=new_version,
        algorithm=f"AES-{key_size * 8}-GCM",
        key_type="data_encryption",
        status=KeyStatus.ACTIVE,
        fingerprint=key_fingerprint(new_version, key_size),
        activated_at=tz.now(),
        usage_count=0,
        rotation_history=[{"action": "generated", "at": tz.now().isoformat(), "predecessor": old_version}],
        notes="Rotated key.",
    )
    KeyActivity.objects.create(
        key_version=new.version,
        action="generated",
        actor=actor,
        status="success",
        message=f"Key {new.version} generated via rotation.",
        metadata={"predecessor": old_version},
    )
    KeyActivity.objects.create(
        key_version=new.version,
        action="activated",
        actor=actor,
        status="success",
        message=f"Key {new.version} activated.",
    )
    from audit.services import create_audit_event

    create_audit_event(
        "key.rotate",
        actor=actor,
        target_type="KeyMetadata",
        target_id=new.id,
        result="success",
        details={"old_version": old_version, "new_version": new_version},
    )
    return new


def get_key_version_for_size(key_size: int) -> str:
    meta = KeyMetadata.objects.filter(status=KeyStatus.ACTIVE, algorithm=f"AES-{key_size * 8}-GCM").first()
    if meta:
        return meta.version
    return "dev-v1"


def record_key_usage(version: str, success: bool = True, actor=None, operation: str = ""):
    obj = KeyMetadata.objects.filter(version=version).first()
    if not obj:
        return
    if success:
        obj.usage_count = (obj.usage_count or 0) + 1
        obj.save(update_fields=["usage_count"])
    else:
        KeyActivity.objects.create(
            key_version=version,
            action="operation_failed",
            actor=actor,
            status="failure",
            message=f"Key operation failed: {operation}",
            metadata={"operation": operation},
        )
        from audit.services import create_security_event

        create_security_event(
            "key_operation_failure",
            actor=actor,
            severity="medium",
            metadata={"key_version": version, "operation": operation},
            risk_score=0.4,
        )


def reconcile_key_usage():
    """Reconcile usage_count with successful EncryptionOperation records (never decreases)."""
    from security.models import EncryptionOperation

    for key in KeyMetadata.objects.all():
        actual = EncryptionOperation.objects.filter(key_version=key.version, success=True).count()
        if actual > (key.usage_count or 0):
            key.usage_count = actual
            key.save(update_fields=["usage_count"])


def key_overview():
    qs = KeyMetadata.objects.all()
    return {
        "total": qs.count(),
        "active": qs.filter(status=KeyStatus.ACTIVE).count(),
        "retired": qs.filter(status=KeyStatus.ROTATED).count(),
        "expired": qs.filter(status=KeyStatus.REVOKED).count() + qs.filter(status=KeyStatus.COMPROMISED).count(),
        "due_for_rotation": qs.filter(status=KeyStatus.ACTIVE, expires_at__isnull=False, expires_at__lte=timezone.now()).count(),
        "failed_operations": KeyActivity.objects.filter(action="operation_failed").count(),
    }