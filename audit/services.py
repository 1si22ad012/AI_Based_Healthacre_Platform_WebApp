import hashlib
import json
from typing import Any, Dict, Optional

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import AuditEvent, SecurityEvent, Severity


def _sanitize(value: Any) -> Any:
    if isinstance(value, (bytes, bytearray)):
        return f"<{len(value)} bytes>"
    if isinstance(value, dict):
        return {k: _sanitize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_sanitize(v) for v in value]
    return value


def client_ip(request) -> Optional[str]:
    if request is None:
        return None
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def create_security_event(
    event_type: str,
    *,
    actor=None,
    severity: str = Severity.INFO,
    request=None,
    metadata: Optional[Dict[str, Any]] = None,
    risk_score: float = 0.0,
) -> SecurityEvent:
    event = SecurityEvent.objects.create(
        actor=actor,
        event_type=event_type,
        severity=severity,
        ip_address=client_ip(request),
        user_agent=(request.META.get("HTTP_USER_AGENT", "")[:500] if request else ""),
        metadata=_sanitize(metadata or {}),
        risk_score=risk_score,
    )
    if severity in ("high", "critical") or event_type in ("anomaly", "access_denied"):
        from .realtime import broadcast_admin_alert

        broadcast_admin_alert({"event_type": event_type, "severity": severity, "risk_score": risk_score, "actor": getattr(actor, "email", None), "created_at": event.created_at.isoformat()})
    return event


def create_audit_event(
    action: str,
    *,
    actor=None,
    target_type: str = "",
    target_id: str = "",
    result: str = "success",
    severity: str = Severity.INFO,
    request=None,
    correlation_id: str = "",
    details: Optional[Dict[str, Any]] = None,
) -> AuditEvent:
    with transaction.atomic():
        last = AuditEvent.objects.order_by("-id").first()
        prev_hash = last.entry_hash if last else ""
        payload = {
            "action": action,
            "actor": getattr(actor, "id", None),
            "target_type": target_type,
            "target_id": str(target_id),
            "result": result,
            "details": _sanitize(details or {}),
            "prev_hash": prev_hash,
            "timestamp": timezone.now().isoformat(),
        }
        entry_hash = hashlib.sha256((prev_hash + json.dumps(payload, sort_keys=True)).encode()).hexdigest()
        event = AuditEvent.objects.create(
            actor=actor,
            action=action,
            target_type=target_type,
            target_id=str(target_id),
            result=result,
            severity=severity,
            ip_address=client_ip(request),
            correlation_id=correlation_id,
            details=_sanitize(details or {}),
            prev_hash=prev_hash,
            entry_hash=entry_hash,
        )
        return event


def notify_user(recipient, title: str, message: str, category: str = "info", url: str = ""):
    from notifications.models import Notification
    from .realtime import broadcast_user_notification

    notification = Notification.objects.create(recipient=recipient, title=title, message=message, category=category, url=url)
    broadcast_user_notification(recipient.id, {"title": title, "message": message, "category": category, "url": url, "id": notification.id})
    return notification
