from datetime import timedelta

from django.utils import timezone

from accounts.models import User
from audit.models import SecurityEvent, AnomalyDetection, AnomalyAlert
from healthcare_ai.models import SecurityIncident
from healthcare_ai.services import calculate_risk_score


def aggregate_user_risk(user, days=30):
    since = timezone.now() - timedelta(days=days)
    events = SecurityEvent.objects.filter(actor=user, created_at__gte=since)
    anomalies = AnomalyDetection.objects.filter(actor=user, created_at__gte=since)
    incidents = SecurityIncident.objects.filter(created_at__gte=since)
    failed_logins = user.failed_login_count
    denied = events.filter(event_type="access_denied").count()
    invalid_tags = 0
    unusual = any(e.created_at.hour < 6 or e.created_at.hour > 22 for e in events)
    anomaly_flag = anomalies.filter(is_anomaly=True).exists()
    features = {
        "failed_logins": failed_logins,
        "denied_requests": denied,
        "invalid_tags": invalid_tags,
        "unusual_hour": unusual,
        "anomaly": anomaly_flag,
    }
    risk = calculate_risk_score(features)
    # historical trend: daily anomaly counts
    trend = {}
    for a in anomalies:
        day = a.created_at.date().isoformat()
        trend[day] = trend.get(day, 0) + (1 if a.is_anomaly else 0)
    return {
        "user": user,
        "risk": risk,
        "event_count": events.count(),
        "anomaly_count": anomalies.count(),
        "incident_count": incidents.count(),
        "trend": trend,
        "factors": risk["reasons"],
    }


def top_risk_accounts(limit=10, days=30):
    users = User.objects.filter(is_active=True)
    results = []
    for u in users:
        agg = aggregate_user_risk(u, days=days)
        results.append(agg)
    results.sort(key=lambda r: r["risk"]["score"], reverse=True)
    return results[:limit]