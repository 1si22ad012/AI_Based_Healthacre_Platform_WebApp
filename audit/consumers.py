import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser


class SecurityAlertConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        if not user or isinstance(user, AnonymousUser) or not user.is_authenticated:
            await self.close(code=4401)
            return
        self.groups_to_join = [f"user_{user.id}"]
        if user.is_superuser or getattr(user, "role", "") == "admin":
            self.groups_to_join.append("admins")
        if getattr(user, "role", "") == "doctor":
            self.groups_to_join.append("doctors")
        for group in self.groups_to_join:
            await self.channel_layer.group_add(group, self.channel_name)
        await self.accept()
        await self.send(text_data=json.dumps({"type": "connection", "status": "connected", "groups": self.groups_to_join}))

    async def disconnect(self, close_code):
        for group in getattr(self, "groups_to_join", []):
            await self.channel_layer.group_discard(group, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        # Support client ping; never accept commands that expose data.
        try:
            data = json.loads(text_data or "{}")
        except json.JSONDecodeError:
            data = {}
        if data.get("type") == "ping":
            await self.send(text_data=json.dumps({"type": "pong"}))

    async def security_event(self, event):
        # Filter sensitive payloads server-side before delivery.
        payload = event.get("payload", {})
        await self.send(text_data=json.dumps({"type": event.get("event_type", "security_event"), "payload": payload}))

    async def notification(self, event):
        await self.send(text_data=json.dumps({"type": "notification", "payload": event.get("payload", {})}))

    async def metric_update(self, event):
        await self.send(text_data=json.dumps({"type": "metric_update", "payload": event.get("payload", {})}))
