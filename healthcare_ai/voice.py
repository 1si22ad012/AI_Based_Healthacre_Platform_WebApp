import re
from typing import Any, Dict, Optional

from django.urls import reverse

ALL_ROLES = {"patient", "doctor", "lab_tech", "admin"}


def normalize_command(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


VOICE_COMMANDS = [
    {
        "name": "dashboard",
        "phrases": ["dashboard", "home", "main page", "my dashboard", "take me home", "show my dashboard", "open dashboard"],
        "url": "/",
        "roles": ALL_ROLES,
        "response": "Opening your dashboard.",
    },
    {
        "name": "appointments",
        "phrases": ["appointments", "appointment", "my appointments", "show my appointments", "open appointments", "view appointments", "see my appointments", "doctor appointments"],
        "url": "/appointments/",
        "roles": {"patient", "doctor", "admin"},
        "response": "Opening your appointments.",
    },
    {
        "name": "book_appointment",
        "phrases": ["book an appointment", "book appointment", "schedule an appointment", "schedule appointment", "request an appointment", "make an appointment"],
        "url": "/appointments/create/",
        "roles": {"patient", "doctor", "admin"},
        "response": "Opening the appointment booking page.",
    },
    {
        "name": "prescriptions",
        "phrases": ["prescriptions", "prescription", "medicines", "medicine", "my medicines", "view my prescription", "do i have any prescriptions", "show my prescriptions"],
        "url": "/prescriptions/",
        "roles": {"patient", "doctor", "admin"},
        "response": "Opening your prescriptions.",
    },
    {
        "name": "patient_records",
        "phrases": ["patient records", "medical records", "health records", "my medical records", "my health records", "open patient records", "show my records", "view my records"],
        "url": "/patients/records/",
        "roles": {"patient", "doctor", "admin"},
        "response": "Opening patient records.",
    },
    {
        "name": "lab_requests",
        "phrases": ["lab requests", "laboratory requests", "test requests", "open laboratory requests"],
        "url": "/laboratory/requests/",
        "roles": {"patient", "doctor", "lab_tech", "admin"},
        "response": "Opening laboratory requests.",
    },
    {
        "name": "lab_reports",
        "phrases": ["lab reports", "test results", "laboratory reports", "open lab reports", "show my test results", "my lab results"],
        "url": "/laboratory/reports/",
        "roles": {"patient", "doctor", "lab_tech", "admin"},
        "response": "Opening laboratory reports.",
    },
    {
        "name": "notifications",
        "phrases": ["notifications", "alerts", "my notifications", "show notifications", "do i have any notifications", "open my alerts", "open alerts"],
        "url": "/notifications/",
        "roles": ALL_ROLES,
        "response": "Opening notifications.",
    },
    {
        "name": "profile",
        "phrases": ["profile", "my profile", "account settings", "open profile"],
        "url": "/profile/",
        "roles": ALL_ROLES,
        "response": "Opening your profile.",
    },
    {
        "name": "password_change",
        "phrases": ["change password", "password change", "update password"],
        "url": "/password-change/",
        "roles": ALL_ROLES,
        "response": "Opening password change.",
    },
    {
        "name": "doctor_search",
        "phrases": ["find a doctor", "search doctors", "doctor search", "find doctor", "search doctors by specialization", "doctors by specialization"],
        "url": "/healthcare/doctor-search/",
        "roles": ALL_ROLES,
        "response": "Opening doctor search.",
    },
    {
        "name": "chatbot",
        "phrases": ["chatbot", "healthcare chatbot", "open healthcare chatbot", "ai assistant", "assistant"],
        "url": "/healthcare/chatbot/",
        "roles": ALL_ROLES,
        "response": "Opening the healthcare chatbot.",
    },
    {
        "name": "symptom_assessment",
        "phrases": ["symptom assessment", "symptom check", "start symptom assessment", "assess symptoms", "symptom checker"],
        "url": "/healthcare/symptom-assessment/",
        "roles": ALL_ROLES,
        "response": "Opening symptom assessment.",
    },
    {
        "name": "face_verification",
        "phrases": ["face verification", "face verify", "biometric verification"],
        "url": "/healthcare/face-verification/",
        "roles": ALL_ROLES,
        "response": "Opening face verification.",
    },
    {
        "name": "security_monitoring",
        "phrases": ["security monitoring", "open security monitoring", "security analytics"],
        "url": "/ai/monitoring/",
        "roles": {"admin"},
        "response": "Opening security monitoring.",
    },
    {
        "name": "anomaly_alerts",
        "phrases": ["anomaly alerts", "open anomaly alerts", "security alerts"],
        "url": "/ai/anomaly-alerts/",
        "roles": {"admin"},
        "response": "Opening anomaly alerts.",
    },
    {
        "name": "encryption_activity",
        "phrases": ["encryption activity", "show encryption activity", "encryption logs"],
        "url": "/security/encryption-activity/",
        "roles": {"admin", "doctor"},
        "response": "Opening encryption activity.",
    },
    {
        "name": "key_management",
        "phrases": ["key management", "manage keys", "encryption keys"],
        "url": "/security/key-management/",
        "roles": {"admin"},
        "response": "Opening key management.",
    },
    {
        "name": "audit_log",
        "phrases": ["audit log", "audit history", "security audit"],
        "url": "/audit/log/",
        "roles": {"admin"},
        "response": "Opening the audit log.",
    },
    {
        "name": "user_management",
        "phrases": ["user management", "manage users", "users"],
        "url": "/users/",
        "roles": {"admin"},
        "response": "Opening user management.",
    },
    {
        "name": "doctor_specialization",
        "phrases": ["doctor specialization", "my specialization", "specialization"],
        "url": "/accounts/doctor-specialization/",
        "roles": {"doctor"},
        "response": "Opening doctor specialization.",
    },
    {
        "name": "risk_analysis",
        "phrases": ["risk analysis", "risk scoring", "security risk"],
        "url": "/healthcare/risk-analysis/",
        "roles": {"admin"},
        "response": "Opening risk analysis.",
    },
    {
        "name": "security_incidents",
        "phrases": ["security incidents", "incident management", "incidents"],
        "url": "/healthcare/security-incidents/",
        "roles": {"admin"},
        "response": "Opening security incidents.",
    },
]

ACTION_COMMANDS = {
    "back": ["go back", "back", "previous page"],
    "scroll_down": ["scroll down", "page down", "go down"],
    "scroll_up": ["scroll up", "page up", "go up"],
    "help": ["help", "commands", "what can you do", "voice commands"],
    "stop": ["stop listening", "close voice assistant", "exit voice assistant", "close assistant"],
}


def resolve_voice_command(transcript: str, role: Optional[str] = None) -> Dict[str, Any]:
    text = normalize_command(transcript)
    role = (role or "").strip().lower()

    if not text:
        return {"action": "none", "message": "I did not hear anything. Please try again."}

    for action, phrases in ACTION_COMMANDS.items():
        if any(phrase in text for phrase in phrases):
            if action == "back":
                return {"action": "back", "message": "Going back."}
            if action == "scroll_down":
                return {"action": "scroll_down", "message": "Scrolling down."}
            if action == "scroll_up":
                return {"action": "scroll_up", "message": "Scrolling up."}
            if action == "help":
                return {
                    "action": "help",
                    "message": "You can say: open dashboard, show my appointments, open prescriptions, show notifications, find a doctor, start symptom assessment, or open healthcare chatbot.",
                }
            if action == "stop":
                return {"action": "stop", "message": "Voice assistant stopped."}

    best_command = None
    best_score = 0
    for command in VOICE_COMMANDS:
        score = 0
        for phrase in command["phrases"]:
            if phrase in text:
                score += max(1, len(phrase.split()))
        if score > best_score:
            best_score = score
            best_command = command

    if best_command is None:
        return {
            "action": "none",
            "message": "I could not understand that. Try saying: show my appointments, open prescriptions, show notifications, or open dashboard.",
        }

    if role and role not in best_command["roles"]:
        return {
            "action": "none",
            "message": f"That page is not available for your role. You can say: show my appointments, open prescriptions, show notifications, or open dashboard.",
        }

    return {
        "action": "navigate",
        "url": best_command["url"],
        "message": best_command["response"],
    }
