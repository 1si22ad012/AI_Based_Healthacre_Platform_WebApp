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
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(email="apiuser@test.com")
        self.assertEqual(user.role, "patient")

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
