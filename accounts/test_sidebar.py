from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User, Role, ApprovalStatus, PatientProfile, DoctorProfile, LabTechProfile


class SidebarRoleTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(email="adm_sb@test.com", password="StrongPass123!", role=Role.ADMIN, is_staff=True, is_superuser=True, is_active=True, approval_status=ApprovalStatus.APPROVED)
        self.doctor = User.objects.create_user(email="doc_sb@test.com", password="StrongPass123!", role=Role.DOCTOR, is_active=True, approval_status=ApprovalStatus.APPROVED)
        DoctorProfile.objects.create(user=self.doctor)
        self.lab = User.objects.create_user(email="lab_sb@test.com", password="StrongPass123!", role=Role.LAB_TECH, is_active=True, approval_status=ApprovalStatus.APPROVED)
        LabTechProfile.objects.create(user=self.lab)
        self.patient = User.objects.create_user(email="pat_sb@test.com", password="StrongPass123!", role=Role.PATIENT, is_active=True, approval_status=ApprovalStatus.APPROVED)
        PatientProfile.objects.create(user=self.patient)
        self.client = Client()

    def _get_dashboard_html(self, user):
        self.client.force_login(user)
        r = self.client.get(reverse("accounts:dashboard"))
        self.assertEqual(r.status_code, 200)
        return r.content.decode()

    def test_patient_sidebar(self):
        html = self._get_dashboard_html(self.patient)
        self.assertIn("My Medical Records", html)
        self.assertNotIn("Key Management", html)
        self.assertNotIn("AI Security Monitoring", html)
        self.assertNotIn("User Management", html)
        self.assertNotIn("Encryption Activity", html)

    def test_doctor_sidebar(self):
        html = self._get_dashboard_html(self.doctor)
        self.assertIn("Patient Records", html)
        self.assertIn("Encryption Activity", html)
        self.assertNotIn("Key Management", html)
        self.assertNotIn("AI Security Monitoring", html)
        self.assertNotIn("User Management", html)

    def test_lab_sidebar(self):
        html = self._get_dashboard_html(self.lab)
        self.assertIn("Assigned Lab Requests", html)
        self.assertNotIn("Key Management", html)
        self.assertNotIn("AI Security Monitoring", html)
        self.assertNotIn("Patient Records", html)

    def test_admin_sidebar(self):
        html = self._get_dashboard_html(self.admin)
        self.assertIn("Key Management", html)
        self.assertIn("AI Security Monitoring", html)
        self.assertIn("User Management", html)
        self.assertIn("Audit Log", html)