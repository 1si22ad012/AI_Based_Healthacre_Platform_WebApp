from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def broadcast(group: str, event_type: str, payload: dict):
    layer = get_channel_layer()
    if layer is None:
        return
    async_to_sync(layer.group_send)(group, {"type": event_type, "payload": payload})


def broadcast_admin_alert(payload: dict):
    broadcast("admins", "security_event", payload)


def broadcast_user_notification(user_id: int, payload: dict):
    broadcast(f"user_{user_id}", "notification", payload)


def broadcast_metric(payload: dict):
    for group in ("admins", "doctors"):
        broadcast(group, "metric_update", payload)
