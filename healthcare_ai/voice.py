import re
from typing import Any, Dict, Optional

from django.urls import reverse

ALL_ROLES = {"patient", "doctor", "lab_tech", "admin"}

FILLER_WORDS = {
    "please", "can", "you", "could", "would", "i", "want", "to", "the", "a", "an",
    "my", "me", "your", "show", "open", "go", "take", "navigate", "view", "display",
}


def normalize_command(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _tokens(text: str):
    return [t for t in text.split() if t]


VOICE_COMMANDS = [
    {"name": "dashboard", "phrases": ["dashboard", "home", "main page", "home page", "my dashboard", "take me home", "show my dashboard", "open dashboard", "go to dashboard", "go home"], "url": "/", "roles": ALL_ROLES, "response": "Opening your dashboard."},
    {"name": "register", "phrases": ["register", "registration", "sign up", "create account", "register page", "open register", "go to register"], "url": "/register/", "roles": {"patient", "doctor", "lab_tech", "admin"}, "response": "Opening the registration page."},
    {"name": "login", "phrases": ["login", "log in", "sign in"], "url": "/login/", "roles": ALL_ROLES, "response": "Opening the login page."},
    {"name": "appointments", "phrases": ["appointments", "appointment", "my appointments", "show my appointments", "open appointments", "view appointments", "see my appointments", "doctor appointments", "bookings", "my bookings", "upcoming appointments", "do i have appointments"], "url": "/appointments/", "roles": {"patient", "doctor", "admin"}, "response": "Opening your appointments."},
    {"name": "book_appointment", "phrases": ["book an appointment", "book appointment", "schedule an appointment", "schedule appointment", "request an appointment", "make an appointment", "new appointment"], "url": "/appointments/create/", "roles": {"patient", "doctor", "admin"}, "response": "Opening the appointment booking page."},
    {"name": "prescriptions", "phrases": ["prescriptions", "prescription", "medicines", "medicine", "my medicines", "view my prescription", "do i have prescriptions", "show my prescriptions", "prescription history", "what medicines"], "url": "/prescriptions/", "roles": {"patient", "doctor", "admin"}, "response": "Opening your prescriptions."},
    {"name": "patient_records", "phrases": ["patient records", "medical records", "health records", "my medical records", "my health records", "open patient records", "show my records", "view my records", "health history", "previous reports", "find my previous reports"], "url": "/patients/records/", "roles": {"patient", "doctor", "admin"}, "response": "Opening patient records."},
    {"name": "lab_requests", "phrases": ["lab requests", "laboratory requests", "test requests", "open laboratory requests", "pending lab requests", "pending tests"], "url": "/laboratory/requests/", "roles": {"patient", "doctor", "lab_tech", "admin"}, "response": "Opening laboratory requests."},
    {"name": "lab_reports", "phrases": ["lab reports", "test results", "laboratory reports", "open lab reports", "show my test results", "my lab results", "show my lab reports", "my reports"], "url": "/laboratory/reports/", "roles": {"patient", "doctor", "lab_tech", "admin"}, "response": "Opening laboratory reports."},
    {"name": "notifications", "phrases": ["notifications", "alerts", "my notifications", "show notifications", "do i have notifications", "open my alerts", "open alerts"], "url": "/notifications/", "roles": ALL_ROLES, "response": "Opening notifications."},
    {"name": "profile", "phrases": ["profile", "my profile", "account settings", "open profile", "my account"], "url": "/profile/", "roles": ALL_ROLES, "response": "Opening your profile."},
    {"name": "password_change", "phrases": ["change password", "password change", "update password"], "url": "/password-change/", "roles": ALL_ROLES, "response": "Opening password change."},
    {"name": "doctor_search", "phrases": ["find a doctor", "search doctors", "doctor search", "find doctor", "find the doctor", "search for a doctor", "show me doctors", "show doctors", "list doctors", "doctors", "doctor", "find a cardiologist", "search for a cardiologist", "find a specialist", "search doctors by specialization", "doctors by specialization"], "url": "/healthcare/doctor-search/", "roles": ALL_ROLES, "response": "Opening doctor search."},
    {"name": "chatbot", "phrases": ["chatbot", "healthcare chatbot", "open healthcare chatbot", "ai assistant", "assistant", "open chatbot"], "url": "/healthcare/chatbot/", "roles": ALL_ROLES, "response": "Opening the healthcare chatbot."},
    {"name": "symptom_assessment", "phrases": ["symptom assessment", "symptom check", "start symptom assessment", "assess symptoms", "symptom checker", "check my symptoms"], "url": "/healthcare/symptom-assessment/", "roles": ALL_ROLES, "response": "Opening symptom assessment."},
    {"name": "face_verification", "phrases": ["face verification", "face verify", "biometric verification"], "url": "/healthcare/face-verification/", "roles": ALL_ROLES, "response": "Opening face verification."},
    {"name": "security_monitoring", "phrases": ["security monitoring", "open security monitoring", "security analytics"], "url": "/ai/monitoring/", "roles": {"admin"}, "response": "Opening security monitoring."},
    {"name": "anomaly_alerts", "phrases": ["anomaly alerts", "open anomaly alerts", "security alerts"], "url": "/ai/anomaly-alerts/", "roles": {"admin"}, "response": "Opening anomaly alerts."},
    {"name": "encryption_activity", "phrases": ["encryption activity", "show encryption activity", "encryption logs"], "url": "/security/encryption-activity/", "roles": {"admin", "doctor"}, "response": "Opening encryption activity."},
    {"name": "key_management", "phrases": ["key management", "manage keys", "encryption keys", "open key management"], "url": "/security/key-management/", "roles": {"admin"}, "response": "Opening key management."},
    {"name": "audit_log", "phrases": ["audit log", "audit history", "security audit", "open audit log"], "url": "/audit/log/", "roles": {"admin"}, "response": "Opening the audit log."},
    {"name": "user_management", "phrases": ["user management", "manage users", "users", "open user management"], "url": "/users/", "roles": {"admin"}, "response": "Opening user management."},
    {"name": "doctor_specialization", "phrases": ["doctor specialization", "my specialization", "specialization", "open specialization"], "url": "/accounts/doctor-specialization/", "roles": {"doctor"}, "response": "Opening doctor specialization."},
    {"name": "risk_analysis", "phrases": ["risk analysis", "risk scoring", "security risk", "open risk analysis"], "url": "/healthcare/risk-analysis/", "roles": {"admin"}, "response": "Opening risk analysis."},
    {"name": "security_incidents", "phrases": ["security incidents", "incident management", "incidents", "open security incidents"], "url": "/healthcare/security-incidents/", "roles": {"admin"}, "response": "Opening security incidents."},
    {"name": "ai_monitoring", "phrases": ["ai security monitoring", "ai monitoring", "open ai monitoring"], "url": "/security/ai-monitoring/", "roles": {"admin"}, "response": "Opening AI security monitoring."},
    {"name": "anomaly_history", "phrases": ["anomaly history", "open anomaly history", "detection history"], "url": "/security/anomaly-history/", "roles": {"admin"}, "response": "Opening anomaly history."},
    {"name": "model_information", "phrases": ["model information", "model info", "open model information"], "url": "/security/model-information/", "roles": {"admin"}, "response": "Opening model information."},
    {"name": "security_incidents_new", "phrases": ["security incidents list", "incidents list"], "url": "/security/incidents/", "roles": {"admin"}, "response": "Opening security incidents."},
    {"name": "risk_dashboard", "phrases": ["risk dashboard", "open risk dashboard"], "url": "/healthcare/risk-dashboard/", "roles": {"admin"}, "response": "Opening risk dashboard."},
]

ACTION_COMMANDS = {
    "back": ["go back", "back", "previous page", "go to previous page"],
    "scroll_down": ["scroll down", "page down", "go down"],
    "scroll_up": ["scroll up", "page up", "go up"],
    "refresh": ["refresh", "refresh page", "reload", "reload page"],
    "help": ["help", "commands", "what can you do", "voice commands", "show help"],
    "stop": ["stop listening", "close voice assistant", "exit voice assistant", "close assistant", "stop"],
}


def _score_command(text: str, command: dict) -> int:
    score = 0
    text_tokens = set(_tokens(text))
    for phrase in command["phrases"]:
        if phrase in text:
            score += len(phrase.split()) * 3
        else:
            ptokens = _tokens(phrase)
            overlap = len(set(ptokens) & text_tokens)
            if overlap:
                score += overlap
    # bonus for name token
    if command["name"].replace("_", " ") in text:
        score += 2
    # Prioritize dashboard when the word dashboard is present (handles speech misrecognition like "open register dashboard").
    if "dashboard" in text_tokens and command["name"] == "dashboard":
        score += 10
    return score


def resolve_voice_command(transcript: str, role: Optional[str] = None) -> Dict[str, Any]:
    text = normalize_command(transcript)
    role = (role or "").strip().lower()

    if not text:
        return {"action": "none", "message": "I did not hear anything. Please try again."}

    # Action commands first
    for action, phrases in ACTION_COMMANDS.items():
        for phrase in phrases:
            if phrase in text:
                if action == "back":
                    return {"action": "back", "message": "Going back."}
                if action == "scroll_down":
                    return {"action": "scroll_down", "message": "Scrolling down."}
                if action == "scroll_up":
                    return {"action": "scroll_up", "message": "Scrolling up."}
                if action == "refresh":
                    return {"action": "refresh", "message": "Refreshing the page."}
                if action == "help":
                    return {"action": "help", "message": "You can say: open dashboard, show my appointments, open prescriptions, show notifications, find a doctor, start symptom assessment, or open healthcare chatbot."}
                if action == "stop":
                    return {"action": "stop", "message": "Voice assistant stopped."}

    best_command = None
    best_score = 0
    for command in VOICE_COMMANDS:
        s = _score_command(text, command)
        if s > best_score:
            best_score = s
            best_command = command

    if best_command is None or best_score < 1:
        return {
            "action": "none",
            "message": "I could not understand that. Try saying: show my appointments, open prescriptions, show notifications, or open dashboard.",
        }

    if role and role not in best_command["roles"]:
        return {
            "action": "none",
            "message": "You do not have permission to access that section.",
        }

    return {
        "action": "navigate",
        "url": best_command["url"],
        "message": best_command["response"],
    }