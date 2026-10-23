from unittest.mock import patch

from django.test import TestCase, Client

from accounts.models import User, PatientProfile, DoctorProfile
from patients.models import MedicalRecord
from patients.services import encrypt_medical_record, decrypt_medical_record


def make_patient(email):
    u = User.objects.create_user(email=email, password="TestPass123!Secure", first_name="P", last_name="Patient", role="patient")
    return PatientProfile.objects.create(user=u), u


def make_doctor(email):
    u = User.objects.create_user(email=email, password="TestPass123!Secure", first_name="D", last_name="Doctor", role="doctor")
    return DoctorProfile.objects.create(user=u), u


class PatientRecordTests(TestCase):
    def setUp(self):
        self.patient_profile, self.patient_user = make_patient("p1@test.com")
        self.other_profile, self.other_user = make_patient("p2@test.com")
        self.doctor_profile, self.doctor_user = make_doctor("d1@test.com")
        from appointments.models import Appointment
        Appointment.objects.create(patient=self.patient_profile, doctor=self.doctor_user, scheduled_at="2026-01-01T10:00:00Z", status="scheduled")

    def test_encrypted_persistence(self):
        record, policy = encrypt_medical_record(self.doctor_user, self.patient_profile, "Note", "Sensitive diagnosis", "high")
        self.assertIsNotNone(record.id)
        # ciphertext should not contain plaintext
        self.assertNotIn(b"Sensitive diagnosis", record.encrypted_content)
        text, _ = decrypt_medical_record(self.doctor_user, record)
        self.assertEqual(text, "Sensitive diagnosis")

    def test_patient_isolation(self):
        record, _ = encrypt_medical_record(self.doctor_user, self.patient_profile, "Note", "Secret", "high")
        with self.assertRaises(PermissionError):
            decrypt_medical_record(self.other_user, record)

    def test_tampering(self):
        record, _ = encrypt_medical_record(self.doctor_user, self.patient_profile, "Note", "Secret", "high")
        record.encrypted_content = bytes([b ^ 1 for b in record.encrypted_content]) if record.encrypted_content else record.encrypted_content
        record.save()
        with self.assertRaises(Exception):
            decrypt_medical_record(self.doctor_user, record)

    def test_authorized_doctor_creates_record(self):
        record, policy = encrypt_medical_record(self.doctor_user, self.patient_profile, "Note", "Secret", "high")
        self.assertTrue(record.id)
        self.assertTrue(policy["allowed"])
        self.assertIn(policy["policy"], ("standard", "strong", "high_security"))

    def test_unauthorized_doctor_denied(self):
        other_doctor_profile, other_doctor = make_doctor("otherdoc@test.com")
        with self.assertRaises(PermissionError):
            encrypt_medical_record(other_doctor, self.patient_profile, "Note", "Secret", "high")

    def test_high_sensitivity_record_allowed(self):
        record, policy = encrypt_medical_record(self.doctor_user, self.patient_profile, "Critical Note", "Secret", "critical")
        self.assertTrue(record.id)
        self.assertTrue(policy["allowed"])

    def test_normal_risk_request_allowed(self):
        record, policy = encrypt_medical_record(self.doctor_user, self.patient_profile, "Note", "Secret", "medium")
        self.assertTrue(policy["allowed"])

    def test_genuinely_anomalous_request_blocked(self):
        with patch("patients.services._recent_security_events", return_value=10):
            with self.assertRaises(PermissionError):
                encrypt_medical_record(self.doctor_user, self.patient_profile, "Note", "Secret", "high")
        from audit.models import SecurityEvent
        self.assertTrue(SecurityEvent.objects.filter(actor=self.doctor_user, event_type="access_denied", metadata__reason="elevated_risk_policy").exists())

    def test_missing_model_artifacts_safe_fallback(self):
        with patch("ai_security.services._model_available", return_value=False), patch("ai_security.services._load", return_value=None):
            record, policy = encrypt_medical_record(self.doctor_user, self.patient_profile, "Note", "Secret", "high")
        self.assertTrue(record.id)
        self.assertTrue(policy["fallback_used"])
        self.assertTrue(policy["allowed"])
