from django.test import TestCase

from ai_security.services import select_policy, detect_anomaly, normalize_policy_features, _model_available, _load
from unittest.mock import patch
import numpy as np


class AITests(TestCase):
    def test_policy_selection_valid(self):
        decision = select_policy({
            "sensitivity": "high",
            "role": "doctor",
            "file_size_kb": 10,
            "cpu_utilization": 20,
            "network_latency": 50,
            "recent_security_events": 0,
            "anomaly_score": 0.1,
            "access_frequency": 2,
            "risk_level": "medium",
        })
        self.assertIn(decision["policy"], ("standard", "strong", "high_security", "elevated_risk"))
        self.assertIn("algorithm", decision)
        self.assertFalse(decision["policy"] == "elevated_risk")

    def test_invalid_features_fallback(self):
        decision = select_policy({"sensitivity": "not-a-level", "role": "unknown"})
        self.assertTrue(decision["fallback_used"] or decision["policy"] in ("high_security", "elevated_risk"))
        self.assertTrue(decision["allowed"])

    def test_critical_sensitivity_elevated(self):
        decision = select_policy({"sensitivity": "critical", "role": "doctor", "risk_level": "critical"})
        self.assertEqual(decision["policy"], "elevated_risk")
        self.assertFalse(decision["allowed"])

    def test_anomaly_detection(self):
        result = detect_anomaly({
            "failed_logins": 0, "login_frequency": 5, "unusual_hour": 0,
            "denied_requests": 0, "upload_size_kb": 200, "record_access_count": 10,
            "cpu_utilization": 30, "encryption_failures": 0, "invalid_tags": 0,
            "suspicious_params": 0,
        })
        self.assertIn("is_anomaly", result)
        self.assertIn("score", result)

    def test_policy_fallback_model_missing(self):
        with patch("ai_security.services._model_available", return_value=False), patch("ai_security.services._load", return_value=None):
            decision = select_policy({"sensitivity": "medium", "role": "doctor"})
        self.assertTrue(decision["fallback_used"])
        self.assertTrue(decision["allowed"])

    def test_anomaly_high(self):
        result = detect_anomaly({
            "failed_logins": 20, "login_frequency": 50, "unusual_hour": 1,
            "denied_requests": 10, "upload_size_kb": 5000, "record_access_count": 100,
            "cpu_utilization": 95, "encryption_failures": 5, "invalid_tags": 3,
            "suspicious_params": 5,
        })
        self.assertTrue(result["is_anomaly"])
