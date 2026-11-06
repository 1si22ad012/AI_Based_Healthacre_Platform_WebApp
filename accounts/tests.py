import re

from django.core import mail
from django.test import TestCase, Client
from django.urls import reverse

from .models import EmailOTP, User, PatientProfile, DoctorProfile, LabTechProfile
from .otp import create_login_otp, generate_otp, verify_login_otp


def make_user(email, role, password="TestPass123!Secure"):
    user = User.objects.create_user(email=email, password=password, first_name="Test", last_name=role, role=role)
    if role == "patient":
        PatientProfile.objects.create(user=user)
    elif role == "doctor":
        DoctorProfile.objects.create(user=user)
    elif role == "lab_tech":
        LabTechProfile.objects.create(user=user)
    return user


def extract_otp(response_or_mailbox):
    text = mail.outbox[-1].body
    match = re.search(r"verification code is: (\d{6})", text)
    assert match, text
    return match.group(1)


class AuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user("patient@test.com", "patient")

    def login_with_otp(self, email, password):
        response = self.client.post(reverse("accounts:login"), {"email": email, "password": password})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("accounts:verify_otp"))
        otp = extract_otp(mail.outbox)
        response = self.client.post(reverse("accounts:verify_otp"), {"otp": otp})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("accounts:dashboard"))
        return response

    def test_valid_login_sends_otp(self):
        response = self.client.post(reverse("accounts:login"), {"email": "patient@test.com", "password": "TestPass123!Secure"})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("accounts:verify_otp"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("verification code", mail.outbox[0].body)
        self.assertNotIn("TestPass123!Secure", mail.outbox[0].body)

    def test_correct_otp_grants_access(self):
        self.client.post(reverse("accounts:login"), {"email": "patient@test.com", "password": "TestPass123!Secure"})
        otp = extract_otp(mail.outbox)
        response = self.client.post(reverse("accounts:verify_otp"), {"otp": otp})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("accounts:dashboard"))

    def test_incorrect_otp_denied(self):
        self.client.post(reverse("accounts:login"), {"email": "patient@test.com", "password": "TestPass123!Secure"})
        response = self.client.post(reverse("accounts:verify_otp"), {"otp": "000000"})
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("patients:records"))
        self.assertEqual(response.status_code, 302)

    def test_expired_otp_rejected(self):
        self.client.post(reverse("accounts:login"), {"email": "patient@test.com", "password": "TestPass123!Secure"})
        otp = extract_otp(mail.outbox)
        record = EmailOTP.objects.filter(user=self.user).latest("created_at")
        record.expires_at = record.created_at
        record.save(update_fields=["expires_at"])
        response = self.client.post(reverse("accounts:verify_otp"), {"otp": otp})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "expired")

    def test_otp_cannot_be_reused(self):
        self.client.post(reverse("accounts:login"), {"email": "patient@test.com", "password": "TestPass123!Secure"})
        otp = extract_otp(mail.outbox)
        first = self.client.post(reverse("accounts:verify_otp"), {"otp": otp})
        self.assertEqual(first.status_code, 302)
        self.client.logout()
        self.client.post(reverse("accounts:login"), {"email": "patient@test.com", "password": "TestPass123!Secure"})
        second_otp = extract_otp(mail.outbox)
        self.assertNotEqual(otp, second_otp)
        response = self.client.post(reverse("accounts:verify_otp"), {"otp": otp})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid")

    def test_resend_generates_new_otp(self):
        self.client.post(reverse("accounts:login"), {"email": "patient@test.com", "password": "TestPass123!Secure"})
        first_otp = extract_otp(mail.outbox)
        from django.utils import timezone
        from datetime import timedelta

        record = EmailOTP.objects.filter(user=self.user).latest("created_at")
        record.last_sent_at = timezone.now() - timedelta(minutes=2)
        record.save(update_fields=["last_sent_at"])
        response = self.client.post(reverse("accounts:resend_otp"))
        self.assertEqual(response.status_code, 302)
        second_otp = extract_otp(mail.outbox)
        self.assertNotEqual(first_otp, second_otp)

    def test_resend_cooldown(self):
        self.client.post(reverse("accounts:login"), {"email": "patient@test.com", "password": "TestPass123!Secure"})
        response = self.client.post(reverse("accounts:resend_otp"))
        self.assertEqual(response.status_code, 302)
        self.assertContains(self.client.get(reverse("accounts:verify_otp")), "wait")

    def test_max_attempts_enforced(self):
        self.client.post(reverse("accounts:login"), {"email": "patient@test.com", "password": "TestPass123!Secure"})
        response = None
        for _ in range(5):
            response = self.client.post(reverse("accounts:verify_otp"), {"otp": "000000"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Maximum")

    def test_login_not_authenticated_before_otp(self):
        self.client.post(reverse("accounts:login"), {"email": "patient@test.com", "password": "TestPass123!Secure"})
        response = self.client.get(reverse("patients:records"))
        self.assertEqual(response.status_code, 302)

    def test_invalid_login(self):
        response = self.client.post(reverse("accounts:login"), {"email": "patient@test.com", "password": "wrong"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid")

    def test_patient_cannot_access_admin_users(self):
        self.login_with_otp("patient@test.com", "TestPass123!Secure")
        response = self.client.get(reverse("accounts:user_management"))
        self.assertEqual(response.status_code, 403)

    def test_dashboard_role(self):
        self.login_with_otp("patient@test.com", "TestPass123!Secure")
        response = self.client.get(reverse("accounts:dashboard"))
        self.assertContains(response, "Patient Dashboard")

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
        # Admin also needs OTP; bypass not possible, so force login.
        self.client.force_login(admin)
        response = self.client.post(reverse("accounts:approve_user", args=[pending.id]))
        self.assertEqual(response.status_code, 302)
        pending.refresh_from_db()
        self.assertTrue(pending.is_active)
        self.assertEqual(pending.approval_status, "approved")

    def test_admin_can_reject_pending_professional(self):
        admin = User.objects.create_superuser(email="rejecter@test.com", password="TestPass123!Secure", first_name="Rejecter", last_name="Admin")
        pending = make_user("reject@test.com", "doctor")
        pending.is_active = False
        pending.approval_status = "pending"
        pending.save(update_fields=["is_active", "approval_status"])
        self.client.force_login(admin)
        response = self.client.post(reverse("accounts:reject_user", args=[pending.id]))
        self.assertEqual(response.status_code, 302)
        pending.refresh_from_db()
        self.assertFalse(pending.is_active)
        self.assertEqual(pending.approval_status, "rejected")

    def test_pending_professional_cannot_access_protected_data(self):
        pending = make_user("pendingaccess@test.com", "doctor")
        pending.is_active = True
        pending.approval_status = "pending"
        pending.save(update_fields=["is_active", "approval_status"])
        self.client.force_login(pending)
        response = self.client.get(reverse("patients:create_record"))
        self.assertEqual(response.status_code, 403)

    def test_otp_cannot_be_used_by_another_user(self):
        make_user("second@test.com", "patient")
        self.client.post(reverse("accounts:login"), {"email": "patient@test.com", "password": "TestPass123!Secure"})
        otp = extract_otp(mail.outbox)
        self.client.post(reverse("accounts:logout"))
        self.client.post(reverse("accounts:login"), {"email": "second@test.com", "password": "TestPass123!Secure"})
        response = self.client.post(reverse("accounts:verify_otp"), {"otp": otp})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid")

    def test_logout_requires_fresh_otp(self):
        self.login_with_otp("patient@test.com", "TestPass123!Secure")
        self.client.logout()
        response = self.client.post(reverse("accounts:login"), {"email": "patient@test.com", "password": "TestPass123!Secure"})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("accounts:verify_otp"))

    def test_otp_service_directly(self):
        user = make_user("directotp@test.com", "patient")
        otp, record = create_login_otp(user)
        success, message = verify_login_otp(user, otp)
        self.assertTrue(success)
        success2, message2 = verify_login_otp(user, otp)
        self.assertFalse(success2)

    def test_email_delivery_failure_does_not_grant_access(self):
        from unittest.mock import patch

        make_user("emailfail@test.com", "patient")
        with patch("accounts.views.send_mail", side_effect=Exception("smtp down")):
            response = self.client.post(reverse("accounts:login"), {"email": "emailfail@test.com", "password": "TestPass123!Secure"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "could not send")
        response = self.client.get(reverse("patients:records"))
        self.assertEqual(response.status_code, 302)