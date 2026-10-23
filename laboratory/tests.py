from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from accounts.models import User, PatientProfile, DoctorProfile, LabTechProfile
from laboratory.models import LabTestRequest, LabReport
from laboratory.services import create_lab_request, upload_report, download_document, decrypt_report


def make_users():
    p = User.objects.create_user(email="pat@test.com", password="TestPass123!Secure", first_name="P", last_name="Patient", role="patient")
    pp = PatientProfile.objects.create(user=p)
    d = User.objects.create_user(email="doc@test.com", password="TestPass123!Secure", first_name="D", last_name="Doctor", role="doctor")
    dp = DoctorProfile.objects.create(user=d)
    t = User.objects.create_user(email="tech@test.com", password="TestPass123!Secure", first_name="T", last_name="Tech", role="lab_tech")
    tp = LabTechProfile.objects.create(user=t)
    return pp, d, t


class LabTests(TestCase):
    def setUp(self):
        self.patient, self.doctor, self.tech = make_users()
        self.lr = create_lab_request(self.doctor, self.patient, "Blood Test", technician=self.tech)

    def test_upload_and_download(self):
        uploaded = SimpleUploadedFile("report.pdf", b"%PDF-1.4 fake", content_type="application/pdf")
        report, doc = upload_report(self.tech, self.lr, uploaded, "Result: normal")
        self.assertEqual(report.status, "submitted")
        text = decrypt_report(self.doctor, report)
        self.assertEqual(text, "Result: normal")
        raw, _ = download_document(self.doctor, doc)
        self.assertEqual(raw, b"%PDF-1.4 fake")

    def test_unauthorized_download(self):
        uploaded = SimpleUploadedFile("report.pdf", b"secret", content_type="application/pdf")
        report, doc = upload_report(self.tech, self.lr, uploaded, "Result")
        other = User.objects.create_user(email="other@test.com", password="TestPass123!Secure", first_name="O", last_name="Other", role="patient")
        PatientProfile.objects.create(user=other)
        with self.assertRaises(PermissionError):
            download_document(other, doc)
