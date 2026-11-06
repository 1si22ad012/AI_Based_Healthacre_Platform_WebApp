from django.test import TestCase
from healthcare_ai.voice import resolve_voice_command, normalize_command


class VoiceUpgradeTests(TestCase):
    def test_natural_variations(self):
        cases = [
            ("open my dashboard", "patient", "navigate", "/"),
            ("take me to the dashboard", "patient", "navigate", "/"),
            ("show my appointments", "patient", "navigate", "/appointments/"),
            ("open prescriptions", "patient", "navigate", "/prescriptions/"),
            ("find a doctor", "patient", "navigate", "/healthcare/doctor-search/"),
            ("go back", "patient", "back", None),
            ("scroll down", "patient", "scroll_down", None),
        ]
        for text, role, action, url in cases:
            r = resolve_voice_command(text, role)
            self.assertEqual(r["action"], action, msg=text)
            if url:
                self.assertEqual(r["url"], url, msg=text)

    def test_unknown_command(self):
        r = resolve_voice_command("xyzzy frobnicate", "patient")
        self.assertEqual(r["action"], "none")

    def test_unauthorized_admin_command_as_patient(self):
        r = resolve_voice_command("open key management", "patient")
        self.assertEqual(r["action"], "none")
        self.assertIn("permission", r["message"])

    def test_admin_allowed(self):
        r = resolve_voice_command("open key management", "admin")
        self.assertEqual(r["action"], "navigate")
        self.assertEqual(r["url"], "/security/key-management/")

    def test_empty(self):
        r = resolve_voice_command("", "patient")
        self.assertEqual(r["action"], "none")

    def test_punctuation_capitalization(self):
        r = resolve_voice_command("Open, My Dashboard!!!", "patient")
        self.assertEqual(r["action"], "navigate")

    def test_register_dashboard_misrecognition(self):
        # "open register dashboard" should still resolve to dashboard
        r = resolve_voice_command("open register dashboard", "patient")
        self.assertEqual(r["action"], "navigate")
        self.assertEqual(r["url"], "/")