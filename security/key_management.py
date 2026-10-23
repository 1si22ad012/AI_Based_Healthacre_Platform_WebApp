import base64
import hashlib

from django.utils import timezone

from .models import KeyMetadata, KeyStatus
from .services import derive_key


def key_fingerprint(version: str, key_size: int = 32) -> str:
    return hashlib.sha256(derive_key(version, key_size)).hexdigest()


def ensure_active_key(version: str = None, key_size: int = 32) -> KeyMetadata:
    from django.conf import settings

    version = version or getattr(settings, "ENCRYPTION_KEY_VERSION", "dev-v1") if hasattr(settings, "ENCRYPTION_KEY_VERSION") else "dev-v1"
    # settings may not define; fallback
    if not version:
        version = "dev-v1"
    obj, created = KeyMetadata.objects.get_or_create(
        version=version,
        defaults={
            "key_id": f"key-{version}",
            "algorithm": f"AES-{key_size * 8}-GCM",
            "status": KeyStatus.ACTIVE,
            "fingerprint": key_fingerprint(version, key_size),
            "notes": "Development key metadata. Production must use a secret manager.",
        },
    )
    if created:
        return obj
    if obj.status != KeyStatus.ACTIVE:
        obj.status = KeyStatus.ACTIVE
        obj.save(update_fields=["status"])
    return obj


def rotate_key(old_version: str, key_size: int = 32) -> KeyMetadata:
    from django.utils import timezone as tz

    new_version = f"v{int(tz.now().timestamp())}"
    old = KeyMetadata.objects.filter(version=old_version).first()
    if old:
        old.status = KeyStatus.ROTATED
        old.rotated_at = tz.now()
        old.save(update_fields=["status", "rotated_at"])
    new = KeyMetadata.objects.create(
        key_id=f"key-{new_version}",
        version=new_version,
        algorithm=f"AES-{key_size * 8}-GCM",
        status=KeyStatus.ACTIVE,
        fingerprint=key_fingerprint(new_version, key_size),
        notes="Rotated key.",
    )
    return new


def get_key_version_for_size(key_size: int) -> str:
    # Prefer an active metadata row matching size; otherwise dev version.
    meta = KeyMetadata.objects.filter(status=KeyStatus.ACTIVE, algorithm=f"AES-{key_size * 8}-GCM").first()
    if meta:
        return meta.version
    return "dev-v1"
