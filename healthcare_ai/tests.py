from django.test import TestCase, Client

from accounts.models import DoctorProfile, Specialization, User
from audit.models import SecurityEvent
from healthcare_ai.models import AIConversation, SecurityIncident, SymptomAssessment
from healthcare_ai.services import incident_events
from healthcare_ai.services import analyze_symptoms, calculate_risk_score, chatbot_response, recommend_doctors, summarize_incident


class HealthcareAITests(TestCase):
    def setUp(self):
        self.specialty = Specialization.objects.create(name="Neurologist")
        self.doctor_user = User.objects.create_user(email="neuro@test.com", password="TestPass123!Secure", first_name="Neuro", last_name="Doctor", role="doctor", is_active=True, approval_status="approved")
        self.doctor = DoctorProfile.objects.create(user=self.doctor_user, specialization=self.specialty, availability="Mon-Fri")

    def test_symptom_classification(self):
        result = analyze_symptoms("persistent headache and difficulty concentrating")
        self.assertIn("Neurologist", result["specialties"])
        self.assertFalse(result["emergency"])

    def test_symptom_combination(self):
        result = analyze_symptoms("chest pain and shortness of breath")
        self.assertIn("Cardiologist", result["specialties"])

    def test_emergency_priority(self):
        result = analyze_symptoms("mild headache but chest pain and difficulty breathing")
        self.assertTrue(result["emergency"])
        self.assertIn("Cardiologist", result["specialties"])

    def test_unknown_symptom_fallback(self):
        result = analyze_symptoms("zzzz unknown symptom")
        self.assertEqual(result["specialties"], ["General Physician"])

    def test_emergency_handling(self):
        result = analyze_symptoms("chest pain and difficulty breathing")
        self.assertTrue(result["emergency"])

    def test_doctor_recommendation(self):
        doctors = list(recommend_doctors(["Neurologist"]))
        self.assertEqual(len(doctors), 1)

    def test_chatbot_no_diagnosis(self):
        response = chatbot_response("Can you diagnose my headache?")
        self.assertIn("cannot diagnose", response.lower())

    def test_risk_scoring(self):
        result = calculate_risk_score({"failed_logins": 5, "denied_requests": 2, "invalid_tags": 1, "anomaly": True})
        self.assertGreaterEqual(result["score"], 60)
        self.assertIn(result["level"], {"medium", "high", "critical"})

    def test_incident_summary(self):
        summary = summarize_incident([{"event_type": "login_failure"}, {"event_type": "login_failure"}])
        self.assertIn("login failure", summary)

    def test_symptom_view_requires_login(self):
        client = Client()
        response = client.get("/healthcare/symptom-assessment/")
        self.assertEqual(response.status_code, 302)

    def test_chatbot_view_creates_conversation(self):
        user = User.objects.create_user(email="patientai@test.com", password="TestPass123!Secure", first_name="Pat", last_name="AI", role="patient")
        client = Client()
        client.login(email=user.email, password="TestPass123!Secure")
        response = client.post("/healthcare/chatbot/", {"message": "Where are appointments?"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(AIConversation.objects.filter(user=user).exists())

    def test_risk_view_admin_only(self):
        user = User.objects.create_user(email="patientrisk@test.com", password="TestPass123!Secure", first_name="Pat", last_name="Risk", role="patient")
        client = Client()
        client.login(email=user.email, password="TestPass123!Secure")
        response = client.get("/healthcare/risk-analysis/")
        self.assertEqual(response.status_code, 403)

    def test_incident_links_security_event(self):
        event = SecurityEvent.objects.create(event_type="anomaly", severity="high", risk_score=0.9, metadata={"reason": "test"})
        incident = SecurityIncident.objects.create(title="Linked incident", severity="high", related_events=[event.id])
        events = incident_events(incident)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["id"], event.id)
        self.assertEqual(events[0]["event_type"], "anomaly")