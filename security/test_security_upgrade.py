from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User, Role, ApprovalStatus


class KeyAndMonitoringAccessTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(email="admin3@test.com", password="StrongPass123!", role=Role.ADMIN, is_staff=True, is_superuser=True, is_active=True, approval_status=ApprovalStatus.APPROVED)
        self.patient = User.objects.create_user(email="pat3@test.com", password="StrongPass123!", role=Role.PATIENT, is_active=True, approval_status=ApprovalStatus.APPROVED)
        self.client = Client()

    def test_admin_dashboards_accessible(self):
        self.client.force_login(self.admin)
        for name in ["security:key_management", "security:ai_monitoring", "security:anomaly_history", "security:incidents", "security:model_information"]:
            r = self.client.get(reverse(name))
            self.assertEqual(r.status_code, 200, msg=f"{name} -> {r.status_code}")

    def test_patient_denied(self):
        self.client.force_login(self.patient)
        for name in ["security:key_management", "security:ai_monitoring", "security:anomaly_history", "security:incidents", "security:model_information"]:
            r = self.client.get(reverse(name))
            self.assertIn(r.status_code, (302, 403), msg=f"{name} -> {r.status_code}")

    def test_key_rotation_admin(self):
        self.client.force_login(self.admin)
        r = self.client.post(reverse("security:rotate_key"), follow=True)
        self.assertEqual(r.status_code, 200)

    def test_key_overview_counts(self):
        from security.key_management import ensure_active_key, key_overview
        ensure_active_key("dev-v1", 32)
        ov = key_overview()
        self.assertIn("total", ov)
        self.assertGreaterEqual(ov["total"], 1)