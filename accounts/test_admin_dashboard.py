from django.test import TestCase, Client
from accounts.models import User, Role, ApprovalStatus


class AdminDashboardAnalyticsTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(email="adm_an@test.com", password="StrongPass123!", role=Role.ADMIN, is_staff=True, is_superuser=True, is_active=True, approval_status=ApprovalStatus.APPROVED)
        self.patient = User.objects.create_user(email="pat_an@test.com", password="StrongPass123!", role=Role.PATIENT, is_active=True, approval_status=ApprovalStatus.APPROVED)
        self.client = Client()

    def test_admin_dashboard_renders_analytics(self):
        self.client.force_login(self.admin)
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "analytics-data")
        self.assertContains(r, "Anomaly Trend")

    def test_patient_cannot_access_admin_dashboard_analytics(self):
        self.client.force_login(self.patient)
        r = self.client.get("/")
        # patient dashboard renders, not admin analytics
        self.assertNotContains(r, "Anomaly Trend")