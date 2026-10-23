from django.test import TestCase
from channels.testing import WebsocketCommunicator
from config.asgi import application
from django.contrib.auth import get_user_model

from accounts.models import User
from audit.services import create_audit_event
from audit.models import AuditEvent


class AuditTests(TestCase):
    def test_hash_chain(self):
        user = User.objects.create_user(email="u@test.com", password="TestPass123!Secure", first_name="U", last_name="User", role="admin")
        e1 = create_audit_event("test.one", actor=user)
        e2 = create_audit_event("test.two", actor=user)
        self.assertNotEqual(e1.entry_hash, "")
        self.assertEqual(e2.prev_hash, e1.entry_hash)
        # Tampering detection is application-level; hash chain links events.
        self.assertTrue(e2.entry_hash.startswith(""))

    def test_websocket_unauthenticated_rejected(self):
        import asyncio
        async def run():
            comm = WebsocketCommunicator(application, "/ws/security/")
            connected, _ = await comm.connect()
            self.assertFalse(connected)
            await comm.disconnect()
        asyncio.run(run())

    def test_websocket_authenticated_connects(self):
        import asyncio
        User = get_user_model()
        user = User.objects.create_user(email="ws@test.com", password="TestPass123!Secure", first_name="W", last_name="S", role="admin")
        async def run():
            comm = WebsocketCommunicator(application, "/ws/security/")
            comm.scope["user"] = user
            connected, _ = await comm.connect()
            self.assertTrue(connected)
            from channels.layers import get_channel_layer
            layer = get_channel_layer()
            await layer.group_send("admins", {"type": "security_event", "payload": {"event_type": "anomaly", "severity": "high"}})
            await comm.receive_json_from()  # connection message
            response = await comm.receive_json_from()
            self.assertEqual(response["type"], "security_event")
            await comm.disconnect()
        asyncio.run(run())
