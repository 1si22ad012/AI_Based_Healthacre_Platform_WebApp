from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User, Role, ApprovalStatus


class AdminPasswordWorkflowTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(email="adminpw@test.com", password="StrongPass123!", role=Role.ADMIN, is_staff=True, is_superuser=True, is_active=True, approval_status=ApprovalStatus.APPROVED)
        self.client = Client()
        self.client.force_login(self.admin)

    def test_create_user_sets_must_change_password(self):
        r = self.client.post(reverse("accounts:user_management"), {
            "first_name": "New",
            "last_name": "Doc",
            "email": "newdoc@test.com",
            "role": Role.DOCTOR,
            "is_active": True,
        })
        self.assertIn(r.status_code, (200, 302))
        u = User.objects.get(email="newdoc@test.com")
        self.assertTrue(u.must_change_password)

    def test_no_hardcoded_password_in_source(self):
        import inspect, accounts.views as v
        src = inspect.getsource(v.user_management_view)
        self.assertNotIn('ChangeMe123!Secure', src)