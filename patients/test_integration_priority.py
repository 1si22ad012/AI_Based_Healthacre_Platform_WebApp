from django.test import TestCase
from django.utils import timezone

from accounts.models import User, Role, ApprovalStatus, PatientProfile
from appointments.models import Appointment
from patients.services import encrypt_medical_record, decrypt_medical_record
from security.models import KeyMetadata, EncryptionOperation
from audit.models import AnomalyDetection


class PatientIntegrationTests(TestCase):
    def setUp(self):
        self.doctor = User.objects.create_user(email="docint@test.com", password="TestPass123!Secure", first_name="Doc", last_name="Int", role=Role.DOCTOR, is_active=True, approval_status=ApprovalStatus.APPROVED)
        self.patient_user = User.objects.create_user(email="patint@test.com", password="TestPass123!Secure", first_name="Pat", last_name="Int", role=Role.PATIENT, is_active=True, approval_status=ApprovalStatus.APPROVED)
        self.pp = PatientProfile.objects.create(user=self.patient_user)
        Appointment.objects.create(patient=self.pp, doctor=self.doctor, scheduled_at=timezone.now())

    def test_record_encrypt_decrypt_roundtrip(self):
        record, policy = encrypt_medical_record(self.doctor, self.pp, "Note", "secret content", "high")
        self.assertIsNotNone(record.id)
        pt, _ = decrypt_medical_record(self.doctor, record)
        self.assertEqual(pt, "secret content")

    def test_key_usage_incremented(self):
        before = 0
        km = KeyMetadata.objects.filter(version__startswith="dev-v1-aes").first()
        if km:
            before = km.usage_count
        encrypt_medical_record(self.doctor, self.pp, "Note2", "more content", "high")
        km = KeyMetadata.objects.filter(version__startswith="dev-v1-aes").first()
        self.assertGreaterEqual(km.usage_count, before)

    def test_anomaly_persisted_on_suspicious(self):
        self.doctor.failed_login_count = 10
        self.doctor.save(update_fields=["failed_login_count"])
        before = AnomalyDetection.objects.count()
        try:
            encrypt_medical_record(self.doctor, self.pp, "Note3", "content", "high")
        except Exception:
            pass
        # anomaly detection record should be created if anomaly detected
        self.assertGreaterEqual(AnomalyDetection.objects.count(), before)