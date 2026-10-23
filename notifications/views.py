from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .models import Notification


@login_required
def notifications_view(request):
    notifications = Notification.objects.filter(recipient=request.user).order_by("-created_at")
    return render(request, "notifications/list.html", {"notifications": notifications})


@login_required
def mark_read_view(request, notification_id):
    notification = Notification.objects.filter(id=notification_id, recipient=request.user).first()
    if notification:
        notification.is_read = True
        notification.save(update_fields=["is_read"])
    return redirect("notifications:list")
