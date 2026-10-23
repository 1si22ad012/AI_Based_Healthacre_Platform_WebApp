from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from audit.models import AnomalyAlert, SecurityEvent
from audit.services import create_audit_event
from .services import detect_anomaly


@login_required
def security_monitoring_view(request):
    events = SecurityEvent.objects.all().order_by("-created_at")[:100]
    alerts = AnomalyAlert.objects.all().order_by("-created_at")[:50]
    return render(request, "ai/security_monitoring.html", {"events": events, "alerts": alerts})


@login_required
def anomaly_alerts_view(request):
    alerts = AnomalyAlert.objects.all().order_by("-created_at")
    if request.method == "POST":
        alert_id = request.POST.get("alert_id")
        action = request.POST.get("action")
        alert = get_object_or_404(AnomalyAlert, id=alert_id)
        if action == "resolve":
            alert.status = "resolved"
            from django.utils import timezone
            alert.resolved_at = timezone.now()
            alert.resolution_notes = request.POST.get("notes", "")
            alert.save(update_fields=["status", "resolved_at", "resolution_notes"])
            create_audit_event("anomaly.resolve", actor=request.user, target_type="AnomalyAlert", target_id=alert.id, request=request, result="success")
            messages.success(request, "Alert resolved.")
        elif action == "investigate":
            alert.status = "investigating"
            alert.assigned_to = request.user
            alert.save(update_fields=["status", "assigned_to"])
            messages.success(request, "Alert assigned.")
        return redirect("ai:anomaly_alerts")
    return render(request, "ai/anomaly_alerts.html", {"alerts": alerts})


@login_required
def detect_demo_view(request):
    if request.method == "POST":
        context = {
            "failed_logins": int(request.POST.get("failed_logins", 0) or 0),
            "login_frequency": int(request.POST.get("login_frequency", 0) or 0),
            "unusual_hour": int(request.POST.get("unusual_hour", 0) or 0),
            "denied_requests": int(request.POST.get("denied_requests", 0) or 0),
            "upload_size_kb": float(request.POST.get("upload_size_kb", 0) or 0),
            "record_access_count": int(request.POST.get("record_access_count", 0) or 0),
            "cpu_utilization": float(request.POST.get("cpu_utilization", 0) or 0),
            "encryption_failures": int(request.POST.get("encryption_failures", 0) or 0),
            "invalid_tags": int(request.POST.get("invalid_tags", 0) or 0),
            "suspicious_params": int(request.POST.get("suspicious_params", 0) or 0),
        }
        result = detect_anomaly(context)
        # Create security event + alert if anomaly.
        from audit.services import create_security_event
        event = create_security_event("anomaly", actor=request.user, request=request, metadata=context, severity="high" if result["is_anomaly"] else "info", risk_score=result["score"])
        if result["is_anomaly"]:
            from audit.models import AnomalyAlert
            alert = AnomalyAlert.objects.create(security_event=event, detector="hybrid", score=result["score"], threshold=result["threshold"], status="open")
            from audit.realtime import broadcast_admin_alert
            broadcast_admin_alert({"type": "anomaly_alert", "alert_id": alert.id, "score": alert.score, "status": alert.status})
            messages.warning(request, "Anomaly detected and alert created.")
        else:
            messages.success(request, "No anomaly detected.")
        return render(request, "ai/detect_demo.html", {"result": result, "context": context})
    return render(request, "ai/detect_demo.html", {"result": None})
