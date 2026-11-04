from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from accounts.permissions import is_admin
from .models import AuditEvent


@login_required
def audit_log_view(request):
    if is_admin(request.user):
        events = AuditEvent.objects.all().order_by("-created_at")
    else:
        events = AuditEvent.objects.filter(actor=request.user).order_by("-created_at")
    action = request.GET.get("action")
    actor = request.GET.get("actor")
    severity = request.GET.get("severity")
    result = request.GET.get("result")
    if action:
        events = events.filter(action__icontains=action)
    if actor:
        events = events.filter(actor__email__icontains=actor)
    if severity:
        events = events.filter(severity=severity)
    if result:
        events = events.filter(result=result)
    return render(request, "audit/audit_log.html", {"events": events[:200]})
