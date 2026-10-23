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
