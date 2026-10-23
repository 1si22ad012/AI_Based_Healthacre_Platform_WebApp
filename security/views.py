from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .models import EncryptionOperation, KeyMetadata
from .key_management import rotate_key
from ai_security.services import select_policy


@login_required
def encryption_activity_view(request):
    ops = EncryptionOperation.objects.all().order_by("-created_at")[:100]
    if not request.user.is_administrator() and not request.user.is_doctor():
        ops = EncryptionOperation.objects.filter(user=request.user).order_by("-created_at")[:100]
    return render(request, "security/encryption_activity.html", {"operations": ops})


@login_required
def key_management_view(request):
    keys = KeyMetadata.objects.all().order_by("-created_at")
    return render(request, "security/key_management.html", {"keys": keys})


@login_required
def rotate_key_view(request):
    if not request.user.is_administrator():
        return render(request, "errors/403.html", status=403)
    if request.method == "POST":
        active = KeyMetadata.objects.filter(status="active").first()
        old_version = active.version if active else "dev-v1-aes256"
        new_key = rotate_key(old_version)
        messages.success(request, f"Rotated to {new_key.version}.")
    return redirect("security:key_management")


@login_required
def policy_demo_view(request):
    if request.method == "POST":
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
