from django.core import mail
from django.test import TestCase, Client
from django.urls import reverse

from .models import User, PatientProfile, DoctorProfile, LabTechProfile




def make_user(email, role, password="TestPass123!Secure"):
    user = User.objects.create_user(email=email, password=password, first_name="Test", last_name=role, role=role)
    if role == "patient":
        PatientProfile.objects.create(user=user)
    elif role == "doctor":
        DoctorProfile.objects.create(user=user)
    elif role == "lab_tech":
        LabTechProfile.objects.create(user=user)
    return user


class AuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user("patient@test.com", "patient")

    def test_valid_login(self):
        response = self.client.post(reverse("accounts:login"), {"email": "patient@test.com", "password": "TestPass123!Secure"})
        self.assertEqual(response.status_code, 302)

    def test_invalid_login(self):
        response = self.client.post(reverse("accounts:login"), {"email": "patient@test.com", "password": "wrong"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid")

    def test_patient_cannot_access_admin_users(self):
        self.client.login(email="patient@test.com", password="TestPass123!Secure")
        response = self.client.get(reverse("accounts:user_management"))
        self.assertEqual(response.status_code, 403)

    def test_dashboard_role(self):
        self.client.login(email="patient@test.com", password="TestPass123!Secure")
        response = self.client.get(reverse("accounts:dashboard"))
        self.assertContains(response, "Patient Dashboard")

    def test_public_registration_creates_patient(self):
        response = self.client.post(reverse("accounts:register"), {
            "first_name": "New",
            "last_name": "Patient",
            "email": "newpatient@test.com",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
            "role": "patient",
        })
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(email="newpatient@test.com")
        self.assertEqual(user.role, "patient")
        self.assertTrue(PatientProfile.objects.filter(user=user).exists())

    def test_public_registration_duplicate_email(self):
        response = self.client.post(reverse("accounts:register"), {
            "first_name": "Dup",
            "last_name": "User",
            "email": "patient@test.com",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already exists")

    def test_public_registration_invalid_password(self):
        response = self.client.post(reverse("accounts:register"), {
            "first_name": "Bad",
            "last_name": "Pass",
            "email": "badpass@test.com",
            "password1": "short",
            "password2": "short",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email="badpass@test.com").exists())

    def test_api_registration_cannot_assign_privileged_role(self):
        response = self.client.post("/api/auth/register/", {
            "email": "apiuser@test.com",
            "first_name": "API",
            "last_name": "User",
            "password": "StrongPass123!",
            "role": "admin",
        }, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(email="apiuser@test.com").exists())

    def test_doctor_login_redirects_to_doctor_dashboard(self):
        make_user("doctor@test.com", "doctor")
        response = self.client.post(reverse("accounts:login"), {"email": "doctor@test.com", "password": "TestPass123!Secure"})
        self.assertEqual(response.status_code, 302)
        response = self.client.get(reverse("accounts:dashboard"))
        self.assertContains(response, "Doctor Dashboard")

    def test_lab_tech_login_redirects_to_lab_dashboard(self):
        make_user("labtech@test.com", "lab_tech")
        response = self.client.post(reverse("accounts:login"), {"email": "labtech@test.com", "password": "TestPass123!Secure"})
        self.assertEqual(response.status_code, 302)
        response = self.client.get(reverse("accounts:dashboard"))
        self.assertContains(response, "Laboratory Dashboard")

    def test_admin_login_redirects_to_admin_dashboard(self):
        admin = User.objects.create_superuser(email="adminrole@test.com", password="TestPass123!Secure", first_name="Admin", last_name="Role")
        response = self.client.post(reverse("accounts:login"), {"email": "adminrole@test.com", "password": "TestPass123!Secure"})
        self.assertEqual(response.status_code, 302)
        response = self.client.get(reverse("accounts:dashboard"))
        self.assertContains(response, "Administrator Dashboard")

    def test_unsupported_role_cannot_access_dashboard(self):
        user = make_user("unknown@test.com", "patient")
        user.role = "unsupported"
        user.save(update_fields=["role"])
        self.client.login(email="unknown@test.com", password="TestPass123!Secure")
        response = self.client.get(reverse("accounts:dashboard"))
        self.assertEqual(response.status_code, 403)

    def test_patient_with_missing_profile_can_access_dashboard(self):
        user = User.objects.create_user(email="missingprofile@test.com", password="TestPass123!Secure", first_name="Missing", last_name="Profile", role="patient")
        self.client.login(email="missingprofile@test.com", password="TestPass123!Secure")
        response = self.client.get(reverse("accounts:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Patient Dashboard")

    def test_doctor_cannot_access_user_management(self):
        make_user("doctorperm@test.com", "doctor")
        self.client.login(email="doctorperm@test.com", password="TestPass123!Secure")
        response = self.client.get(reverse("accounts:user_management"))
        self.assertEqual(response.status_code, 403)

    def test_login_sends_email_notification(self):
        make_user("loginemail@test.com", "patient")
        response = self.client.post(reverse("accounts:login"), {"email": "loginemail@test.com", "password": "TestPass123!Secure"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("login was recorded", mail.outbox[0].body)
        self.assertNotIn("TestPass123!Secure", mail.outbox[0].body)

    def test_public_doctor_registration_is_pending(self):
        response = self.client.post(reverse("accounts:register"), {
            "first_name": "Pending",
            "last_name": "Doctor",
            "email": "pendingdoctor@test.com",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
            "role": "doctor",
        })
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(email="pendingdoctor@test.com")
        self.assertEqual(user.role, "doctor")
        self.assertFalse(user.is_active)
        self.assertEqual(user.approval_status, "pending")
        # Pending professionals cannot log in.
        login_response = self.client.post(reverse("accounts:login"), {"email": "pendingdoctor@test.com", "password": "StrongPass123!"})
        self.assertEqual(login_response.status_code, 200)
        self.assertContains(login_response, "pending")

    def test_public_labtech_registration_is_pending(self):
        response = self.client.post(reverse("accounts:register"), {
            "first_name": "Pending",
            "last_name": "Lab",
            "email": "pendinglab@test.com",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
            "role": "lab_tech",
        })
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(email="pendinglab@test.com")
        self.assertEqual(user.role, "lab_tech")
        self.assertFalse(user.is_active)
        self.assertEqual(user.approval_status, "pending")

    def test_admin_can_approve_pending_professional(self):
        admin = User.objects.create_superuser(email="approver@test.com", password="TestPass123!Secure", first_name="Approver", last_name="Admin")
        pending = make_user("approve@test.com", "doctor")
        pending.is_active = False
        pending.approval_status = "pending"
        pending.save(update_fields=["is_active", "approval_status"])
        self.client.login(email="approver@test.com", password="TestPass123!Secure")
        response = self.client.post(reverse("accounts:approve_user", args=[pending.id]))
        self.assertEqual(response.status_code, 302)
        pending.refresh_from_db()
        self.assertTrue(pending.is_active)
        self.assertEqual(pending.approval_status, "approved")
        self.assertEqual(pending.approved_by, admin)

    def test_admin_can_reject_pending_professional(self):
        admin = User.objects.create_superuser(email="rejecter@test.com", password="TestPass123!Secure", first_name="Rejecter", last_name="Admin")
        pending = make_user("reject@test.com", "doctor")
        pending.is_active = False
        pending.approval_status = "pending"
        pending.save(update_fields=["is_active", "approval_status"])
        self.client.login(email="rejecter@test.com", password="TestPass123!Secure")
        response = self.client.post(reverse("accounts:reject_user", args=[pending.id]))
        self.assertEqual(response.status_code, 302)
        pending.refresh_from_db()
        self.assertFalse(pending.is_active)
        self.assertEqual(pending.approval_status, "rejected")

    def test_pending_professional_cannot_access_protected_data(self):
        pending = make_user("pendingaccess@test.com", "doctor")
        pending.is_active = False
        pending.approval_status = "pending"
        pending.save(update_fields=["is_active", "approval_status"])
        # Even if a pending account were active, role checks require approval.
        pending.is_active = True
        pending.save(update_fields=["is_active"])
        self.assertFalse(pending.is_doctor())
        self.client.force_login(pending)
        response = self.client.get(reverse("patients:create_record"))
        self.assertEqual(response.status_code, 403)
