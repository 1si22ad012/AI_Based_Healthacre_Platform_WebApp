from .models import Notification


def notifications(request):
    if request.user.is_authenticated:
        unread = Notification.objects.filter(recipient=request.user, is_read=False).count()
        recent = Notification.objects.filter(recipient=request.user).select_related()[:5]
    else:
        unread = 0
        recent = []
    return {"unread_notifications": unread, "recent_notifications": recent}
