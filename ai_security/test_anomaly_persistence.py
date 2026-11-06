from django.test import TestCase
from accounts.models import User, Role, ApprovalStatus
from ai_security.services import extract_security_features, detect_anomaly, persist_anomaly_detection
from audit.models import AnomalyDetection, AnomalyAlert
from healthcare_ai.models import SecurityIncident


class AnomalyPersistenceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="anomtest2@test.com", password="StrongPass123!", role=Role.DOCTOR, is_active=True, approval_status=ApprovalStatus.APPROVED)

    def test_anomalous_persists_event_alert_incident(self):
        ctx = {"failed_logins": 9, "login_frequency": 25, "unusual_hour": 1, "denied_requests": 7,
               "upload_size_kb": 5000, "record_access_count": 50, "cpu_utilization": 90,
               "encryption_failures": 4, "invalid_tags": 3, "suspicious_params": 5}
        features = extract_security_features(ctx)
        result = detect_anomaly(features)
        self.assertTrue(result["is_anomaly"])
        det = persist_anomaly_detection(features, result, actor=self.user, event_type="test")
        self.assertIsNotNone(det)
        self.assertTrue(det.is_anomaly)
        self.assertGreaterEqual(AnomalyDetection.objects.count(), 1)
        self.assertGreaterEqual(AnomalyAlert.objects.count(), 1)
        self.assertGreaterEqual(SecurityIncident.objects.count(), 1)

    def test_normal_does_not_create_alert(self):
        ctx = {k: 0 for k in ["failed_logins", "login_frequency", "unusual_hour", "denied_requests",
               "upload_size_kb", "record_access_count", "cpu_utilization", "encryption_failures",
               "invalid_tags", "suspicious_params"]}
        ctx["upload_size_kb"] = 1.0
        features = extract_security_features(ctx)
        result = detect_anomaly(features)
        before = AnomalyAlert.objects.count()
        persist_anomaly_detection(features, result, actor=self.user, event_type="test_normal")
        self.assertEqual(AnomalyAlert.objects.count(), before)

    def test_missing_values_handled(self):
        features = extract_security_features({})
        self.assertEqual(features["failed_logins"], 0.0)
        result = detect_anomaly(features)
        self.assertIn("is_anomaly", result)