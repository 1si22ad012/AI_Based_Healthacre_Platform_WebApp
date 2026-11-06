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
        try:
            from accounts.models import User
            from notifications.models import Notification

            for admin_user in User.objects.filter(role="admin") | User.objects.filter(is_superuser=True):
                Notification.objects.create(
                    recipient=admin_user,
                    title="Security event requires review",
                    message=f"{event_type} with {severity} severity was recorded.",
                    category="security",
                    url="/ai/monitoring/",
                )
            from healthcare_ai.services import create_incident_for_security_event

            create_incident_for_security_event(event)
        except Exception as exc:
            import logging

            logging.getLogger(__name__).warning("Incident/notification creation failed for security event %s: %s", event.id, exc)
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


def admin_analytics(days=30):
    from datetime import timedelta
    from django.utils import timezone
    from django.db.models import Avg, Count
    from audit.models import AnomalyDetection, SecurityEvent, AnomalyAlert
    from healthcare_ai.models import SecurityIncident
    from security.models import KeyMetadata, EncryptionOperation

    since = timezone.now() - timedelta(days=days)
    events = SecurityEvent.objects.filter(created_at__gte=since)
    detections = AnomalyDetection.objects.filter(created_at__gte=since)

    # anomaly trend by day
    trend = {}
    for d in detections:
        day = d.created_at.date().isoformat()
        bucket = trend.setdefault(day, {"normal": 0, "anomalous": 0})
        if d.is_anomaly:
            bucket["anomalous"] += 1
        else:
            bucket["normal"] += 1
    trend_labels = sorted(trend.keys())
    trend_normal = [trend[day]["normal"] for day in trend_labels]
    trend_anomalous = [trend[day]["anomalous"] for day in trend_labels]

    # events by type
    events_by_type = dict(events.values_list("event_type").annotate(c=Count("id")).values_list("event_type", "c"))

    # risk distribution based on AnomalyDetection.risk_score
    risk_dist = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    for d in detections:
        s = d.risk_score or 0
        if s >= 75:
            risk_dist["critical"] += 1
        elif s >= 50:
            risk_dist["high"] += 1
        elif s >= 25:
            risk_dist["medium"] += 1
        else:
            risk_dist["low"] += 1

    # high-risk accounts
    try:
        from healthcare_ai.risk_history import top_risk_accounts
        high_risk_accounts = top_risk_accounts(limit=10, days=days)
    except Exception:
        high_risk_accounts = []

    avg_risk = detections.aggregate(avg=Avg("risk_score"))["avg"] or 0.0

    stats = {
        "total_security_events": events.count(),
        "total_anomaly_detections": detections.count(),
        "normal_activities": detections.filter(is_anomaly=False).count(),
        "anomalous_activities": detections.filter(is_anomaly=True).count(),
        "open_incidents": SecurityIncident.objects.filter(status__in=["new", "under_investigation", "acknowledged"]).count(),
        "critical_incidents": SecurityIncident.objects.filter(severity="critical").count(),
        "high_risk_accounts_count": len([a for a in high_risk_accounts if a["risk"]["score"] >= 50]),
        "average_risk_score": round(float(avg_risk), 2),
        "active_keys": KeyMetadata.objects.filter(status="active").count(),
        "failed_encryption_operations": EncryptionOperation.objects.filter(success=False).count(),
    }

    return {
        "stats": stats,
        "days": days,
        "trend_labels": trend_labels,
        "trend_normal": trend_normal,
        "trend_anomalous": trend_anomalous,
        "events_by_type": events_by_type,
        "risk_distribution": risk_dist,
        "high_risk_accounts": high_risk_accounts,
    }


def notify_user(recipient, title: str, message: str, category: str = "info", url: str = ""):
    from notifications.models import Notification
    from .realtime import broadcast_user_notification

    notification = Notification.objects.create(recipient=recipient, title=title, message=message, category=category, url=url)
    broadcast_user_notification(recipient.id, {"title": title, "message": message, "category": category, "url": url, "id": notification.id})
    return notification
