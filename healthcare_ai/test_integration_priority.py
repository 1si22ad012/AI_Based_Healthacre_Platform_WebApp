from django.test import TestCase
from django.core import mail

from accounts.models import User, Role, ApprovalStatus
from healthcare_ai.models import ChatConversation, ChatMessage, SymptomAssessment
from healthcare_ai.services import analyze_symptoms, chatbot_answer
from healthcare_ai.rag import retrieve, seed_knowledge


class IntegrationPriorityTests(TestCase):
    def setUp(self):
        seed_knowledge()
        self.user = User.objects.create_user(email="intpat@test.com", password="TestPass123!Secure", first_name="Pat", last_name="Int", role=Role.PATIENT, is_active=True, approval_status=ApprovalStatus.APPROVED)
        self.other = User.objects.create_user(email="intother@test.com", password="TestPass123!Secure", first_name="Other", last_name="User", role=Role.PATIENT, is_active=True, approval_status=ApprovalStatus.APPROVED)

    def test_rag_retrieval_returns_sources(self):
        results = retrieve("fever and chest pain")
        self.assertGreater(len(results), 0)
        self.assertIn("source_title", results[0])

    def test_chatbot_answer_stores_conversation_and_sources(self):
        text, sources, conv = chatbot_answer("What is fever?", self.user)
        self.assertTrue(conv is not None)
        self.assertEqual(conv.user, self.user)
        self.assertTrue(ChatMessage.objects.filter(conversation=conv, role="assistant").exists())
        # no LLM configured -> fallback used, but conversation stored
        self.assertTrue(len(text) > 0)

    def test_conversation_ownership_isolation(self):
        _, _, conv = chatbot_answer("Hello", self.user)
        # other user cannot access
        self.assertFalse(ChatConversation.objects.filter(id=conv.id, user=self.other).exists())

    def test_symptom_assessment_structured_fields(self):
        data = {
            "symptoms": "chest pain and shortness of breath",
            "duration": "2 days",
            "severity": "severe",
            "medical_history": "hypertension",
        }
        analysis = analyze_symptoms(data)
        self.assertTrue(analysis["emergency"])
        self.assertIn("Cardiologist", analysis["specialties"])
        self.assertEqual(analysis["recommended_urgency"], "emergency")
        assessment = SymptomAssessment.objects.create(
            patient=self.user, symptoms=data["symptoms"], duration=data["duration"],
            severity=data["severity"], medical_history=data["medical_history"],
            predicted_specialties=analysis["specialties"], emergency=analysis["emergency"],
            recommended_urgency=analysis["recommended_urgency"], explanation=analysis["explanation"],
        )
        self.assertEqual(assessment.patient, self.user)
        self.assertEqual(assessment.duration, "2 days")

    def test_llm_fallback_without_credentials(self):
        from django.conf import settings
        self.assertFalse(bool(getattr(settings, "LLM_API_KEY", "")))
        text, sources, conv = chatbot_answer("Tell me about diabetes", self.user)
        self.assertTrue(len(text) > 0)