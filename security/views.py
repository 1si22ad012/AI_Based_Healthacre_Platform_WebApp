import json
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from accounts.permissions import is_admin
from .models import EncryptionOperation, KeyActivity, KeyMetadata
from .key_management import key_overview, rotate_key
from ai_security.services import ANOMALY_FEATURE_NAMES, detect_anomaly, extract_security_features
from audit.models import AnomalyDetection, SecurityEvent, AnomalyAlert
from healthcare_ai.models import SecurityIncident

logger = logging.getLogger(__name__)


def _admin_required(request):
    if not is_admin(request.user):
        return render(request, "errors/403.html", status=403)
    return None


@login_required
def encryption_activity_view(request):
    ops = EncryptionOperation.objects.all().order_by("-created_at")[:100]
    if not request.user.is_administrator() and not request.user.is_doctor():
        ops = EncryptionOperation.objects.filter(user=request.user).order_by("-created_at")[:100]
    return render(request, "security/encryption_activity.html", {"operations": ops})


@login_required
def key_management_view(request):
    denied = _admin_required(request)
    if denied:
        return denied
    from .key_management import key_overview

    keys = KeyMetadata.objects.all().order_by("-created_at")
    for key in keys:
        if key.activated_at is None:
            key.activated_at = key.created_at
    activities = KeyActivity.objects.all().order_by("-created_at")[:50]
    return render(
        request,
        "security/key_management.html",
        {
            "keys": keys,
            "overview": key_overview(),
            "activities": activities,
        },
    )


@login_required
def rotate_key_view(request):
    denied = _admin_required(request)
    if denied:
        return denied
    if request.method == "POST":
        active = KeyMetadata.objects.filter(status="active").first()
        old_version = active.version if active else "dev-v1-aes256"
        try:
            new_key = rotate_key(old_version, actor=request.user)
            messages.success(request, f"Rotated to {new_key.version}.")
        except Exception as exc:
            logger.exception("Key rotation failed: %s", exc)
            messages.error(request, "Key rotation failed. See logs for details.")
    return redirect("security:key_management")


@login_required
def policy_demo_view(request):
    if request.method == "POST":
        from ai_security.services import select_policy

        context = {
            "sensitivity": request.POST.get("sensitivity", "high"),
            "role": request.user.role,
            "file_size_kb": float(request.POST.get("file_size_kb", 0) or 0),
            "cpu_utilization": float(request.POST.get("cpu_utilization", 0) or 0),
            "network_latency": float(request.POST.get("network_latency", 0) or 0),
            "recent_security_events": int(request.POST.get("recent_security_events", 0) or 0),
            "anomaly_score": float(request.POST.get("anomaly_score", 0) or 0),
            "access_frequency": int(request.POST.get("access_frequency", 0) or 0),
            "risk_level": request.POST.get("risk_level", "medium"),
        }
        decision = select_policy(context)
        return render(request, "security/policy_demo.html", {"decision": decision, "context": context})
    return render(request, "security/policy_demo.html", {"decision": None})


@login_required
def ai_monitoring_view(request):
    denied = _admin_required(request)
    if denied:
        return denied
    events = SecurityEvent.objects.all().order_by("-created_at")[:100]
    alerts = AnomalyAlert.objects.all().order_by("-created_at")[:50]
    detections = AnomalyDetection.objects.all().order_by("-created_at")[:50]
    incidents = SecurityIncident.objects.all().order_by("-created_at")[:50]
    from security.key_management import key_overview

    overview = {
        "total_events": SecurityEvent.objects.count(),
        "total_anomalies": AnomalyDetection.objects.filter(is_anomaly=True).count(),
        "total_detections": AnomalyDetection.objects.count(),
        "normal_activities": AnomalyDetection.objects.filter(is_anomaly=False).count(),
        "high_risk": SecurityEvent.objects.filter(severity="high").count() + SecurityEvent.objects.filter(severity="critical").count(),
        "critical_incidents": SecurityIncident.objects.filter(severity="critical").count(),
        "open_incidents": SecurityIncident.objects.filter(status__in=["new", "under_investigation", "acknowledged"]).count(),
        "resolved_incidents": SecurityIncident.objects.filter(status="resolved").count(),
        "active_keys": KeyMetadata.objects.filter(status="active").count(),
    }
    return render(
        request,
        "security/ai_monitoring.html",
        {
            "events": events,
            "alerts": alerts,
            "detections": detections,
            "incidents": incidents,
            "overview": overview,
        },
    )


@login_required
def anomaly_history_view(request):
    denied = _admin_required(request)
    if denied:
        return denied
    qs = AnomalyDetection.objects.all().order_by("-created_at")
    role = request.GET.get("role")
    severity = request.GET.get("severity")
    status_filter = request.GET.get("status")
    result_filter = request.GET.get("result")  # anomaly/normal
    algorithm = request.GET.get("algorithm")
    if role:
        qs = qs.filter(user_role=role)
    if severity:
        qs = qs.filter(risk_level=severity)
    if status_filter:
        qs = qs.filter(detection_status=status_filter)
    if result_filter == "anomaly":
        qs = qs.filter(is_anomaly=True)
    elif result_filter == "normal":
        qs = qs.filter(is_anomaly=False)
    detections = qs[:200]
    return render(request, "security/anomaly_history.html", {"detections": detections, "filters": request.GET})


@login_required
def anomaly_detail_view(request, detection_id):
    denied = _admin_required(request)
    if denied:
        return denied
    detection = get_object_or_404(AnomalyDetection, id=detection_id)
    return render(request, "security/anomaly_detail.html", {"detection": detection})


@login_required
def security_incidents_view(request):
    denied = _admin_required(request)
    if denied:
        return denied
    incidents = SecurityIncident.objects.all().order_by("-created_at")
    if request.method == "POST":
        incident_id = request.POST.get("incident_id")
        action = request.POST.get("action")
        incident = SecurityIncident.objects.filter(id=incident_id).first()
        if incident:
            if action == "acknowledge":
                incident.status = "acknowledged"
                from django.utils import timezone

                incident.acknowledged_at = timezone.now()
            elif action == "investigate":
                incident.status = "under_investigation"
            elif action == "resolve":
                incident.status = "resolved"
                from django.utils import timezone

                incident.resolved_at = timezone.now()
            elif action == "false_positive":
                incident.status = "false_positive"
            incident.assigned_to = request.user
            note = request.POST.get("note", "").strip()
            if note:
                history = list(incident.history or [])
                history.append({"action": action, "by": request.user.email, "note": note, "at": timezone.now().isoformat()})
                incident.history = history
            incident.save()
            from audit.services import create_audit_event

            create_audit_event(
                f"incident.{action}",
                actor=request.user,
                target_type="SecurityIncident",
                target_id=incident.id,
                request=request,
                result="success",
                details={"note": note},
            )
            messages.success(request, "Incident updated.")
            return redirect("security:incidents")
    return render(request, "security/incidents.html", {"incidents": incidents})


@login_required
def model_information_view(request):
    denied = _admin_required(request)
    if denied:
        return denied
    from ai_security.services import MODEL_VERSION, ANOMALY_MODEL_VERSION
    registry = {}
    try:
        import json
        from pathlib import Path
        from django.conf import settings
        reg_path = Path(settings.ML_ARTIFACT_DIR) / "model_registry.json"
        if reg_path.exists():
            registry = json.loads(reg_path.read_text())
    except Exception:
        registry = {}

    info = {
        "policy_model": {
            "name": "policy_random_forest.joblib",
            "algorithm": "Random Forest Classifier",
            "version": MODEL_VERSION,
            "features": [
                "sensitivity (0-3)",
                "role (0-3)",
                "file_size_kb",
                "cpu_utilization",
                "network_latency",
                "recent_security_events",
                "anomaly_score",
                "access_frequency",
                "risk_level (0-3)",
            ],
            "dataset": "Synthetic, 4000 rows generated in ai_security/training.py",
            "threshold": "confidence >= 0.55 else fallback; mandatory elevated if risk critical/anomaly>=0.85/events>=8",
            "status": "active" if True else "inactive",
        },
        "anomaly_models": [
            {
                "name": "isolation_forest.joblib",
                "algorithm": "Isolation Forest",
                "version": ANOMALY_MODEL_VERSION,
                "features": ANOMALY_FEATURE_NAMES,
                "dataset": "Synthetic normal (3000+ low-activity) rows; contamination=0.1",
                "threshold": "combined score >= 0.5",
                "status": "active",
            },
            {
                "name": "one_class_svm.joblib",
                "algorithm": "One-Class SVM (RBF)",
                "version": ANOMALY_MODEL_VERSION,
                "features": ANOMALY_FEATURE_NAMES,
                "dataset": "Synthetic normal rows; nu=0.1",
                "threshold": "combined score >= 0.5",
                "status": "active",
            },
            {
                "name": "anomaly_random_forest.joblib",
                "algorithm": "Random Forest Classifier",
                "version": ANOMALY_MODEL_VERSION,
                "features": ANOMALY_FEATURE_NAMES,
                "dataset": "Synthetic normal + attack (600) rows; balanced",
                "threshold": "probability >= 0.5",
                "status": "active",
            },
        ],
        "feature_descriptions": {
            "failed_logins": "Number of failed login attempts for the actor.",
            "login_frequency": "Recent suspicious security events in last hour.",
            "unusual_hour": "1 if activity outside 06:00-22:00.",
            "denied_requests": "Denied request count.",
            "upload_size_kb": "Upload size in KB.",
            "record_access_count": "Number of records for patient.",
            "cpu_utilization": "Reported CPU utilization.",
            "encryption_failures": "Failed encryption operations for user.",
            "invalid_tags": "Invalid AES-GCM tag count.",
            "suspicious_params": "Suspicious parameter count.",
        },
        "last_prediction": AnomalyDetection.objects.order_by("-created_at").first(),
        "registry": registry,
    }
    return render(request, "security/model_information.html", {"info": info})