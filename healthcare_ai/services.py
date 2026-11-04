import re
from typing import Dict, List

from django.utils import timezone

from accounts.models import DoctorProfile, Specialization
from django.contrib.auth import get_user_model

User = get_user_model()

SYMPTOM_MAP = {
    "neurologist": ["headache", "migraine", "dizziness", "concentration", "seizure", "numbness", "memory"],
    "cardiologist": ["chest pain", "palpitation", "heart", "blood pressure", "shortness of breath"],
    "dermatologist": ["rash", "itching", "skin", "acne", "eczema"],
    "orthopedic specialist": ["joint", "bone", "fracture", "back pain", "knee", "sprain"],
    "gastroenterologist": ["stomach", "nausea", "vomiting", "diarrhea", "abdominal", "digestion"],
    "pulmonologist": ["cough", "breathing", "lung", "asthma", "wheeze"],
    "psychiatrist": ["anxiety", "depression", "stress", "panic", "insomnia", "mood"],
    "ent specialist": ["ear", "throat", "nose", "sinus", "hearing"],
    "ophthalmologist": ["eye", "vision", "blur", "sight"],
    "gynecologist": ["pregnancy", "menstrual", "pelvic", "ovarian"],
    "pediatrician": ["child", "infant", "baby"],
    "general physician": ["fever", "fatigue", "cold", "flu", "weakness", "infection"],
}

EMERGENCY_KEYWORDS = [
    "chest pain", "difficulty breathing", "shortness of breath", "unconscious",
    "seizure", "stroke", "suicidal", "severe bleeding", "loss of consciousness",
]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def analyze_symptoms(symptoms: str) -> Dict[str, object]:
    text = _normalize(symptoms)
    emergency = any(keyword in text for keyword in EMERGENCY_KEYWORDS)
    matches = []
    for specialty, keywords in SYMPTOM_MAP.items():
        score = sum(1 for keyword in keywords if keyword in text)
        if score:
            matches.append((specialty, score))
    matches.sort(key=lambda item: item[1], reverse=True)
    specialties = [item[0].title() for item in matches[:3]]
    if not specialties:
        specialties = ["General Physician"]
    explanation = (
        "The symptoms were matched to possible specialties using a transparent keyword-based classifier. "
        "This is preliminary navigation only and not a diagnosis."
    )
    if emergency:
        explanation += " Emergency symptoms may be present; seek immediate medical care."
    return {
        "specialties": specialties,
        "emergency": emergency,
        "explanation": explanation,
    }


def recommend_doctors(specialties: List[str]):
    names = [name.strip() for name in specialties]
    return DoctorProfile.objects.filter(
        specialization__name__in=names,
        user__is_active=True,
        user__approval_status="approved",
    ).select_related("user", "specialization")


def chatbot_response(message: str, user=None) -> str:
    text = _normalize(message)
    if "appointment" in text:
        return "You can request or view appointments from the Appointments page. Please consult a qualified healthcare professional for medical advice."
    if "prescription" in text:
        return "Prescriptions are available in the Prescriptions section after your doctor issues them. This assistant cannot prescribe medication."
    if "record" in text:
        return "Medical records are encrypted and available only to authorized users. Please consult your healthcare provider for interpretation."
    if "doctor" in text or "specialist" in text:
        return "You can search doctors by specialization and request an appointment. This assistant does not provide diagnoses."
    if "emergency" in text:
        return "If you may be experiencing a medical emergency, contact local emergency services immediately."
    return "I can help with general healthcare information, app navigation, appointments, and doctor search. I cannot diagnose conditions or recommend treatment. Please consult a qualified healthcare professional."


def calculate_risk_score(event: Dict[str, object]) -> Dict[str, object]:
    score = 0
    reasons = []
    failed = int(event.get("failed_logins", 0) or 0)
    denied = int(event.get("denied_requests", 0) or 0)
    invalid_tags = int(event.get("invalid_tags", 0) or 0)
    unusual_hour = bool(event.get("unusual_hour", False))
    anomaly = bool(event.get("anomaly", False))
    if failed:
        score += min(30, failed * 6)
        reasons.append(f"{failed} failed login attempt(s)")
    if denied:
        score += min(25, denied * 5)
        reasons.append(f"{denied} denied request(s)")
    if invalid_tags:
        score += min(25, invalid_tags * 8)
        reasons.append(f"{invalid_tags} invalid authentication tag(s)")
    if unusual_hour:
        score += 10
        reasons.append("activity occurred at an unusual hour")
    if anomaly:
        score += 25
        reasons.append("anomaly detector flagged the event")
    score = min(100, score)
    if score >= 80:
        level = "critical"
    elif score >= 60:
        level = "high"
    elif score >= 30:
        level = "medium"
    else:
        level = "low"
    return {"score": score, "level": level, "reasons": reasons}


def explain_risk(features: Dict[str, object]) -> List[str]:
    return calculate_risk_score(features)["reasons"] or ["No significant risk indicators were identified."]


def incident_events(incident) -> List[Dict[str, object]]:
    from audit.models import SecurityEvent

    event_ids = [int(value) for value in (incident.related_events or []) if str(value).isdigit()]
    events = SecurityEvent.objects.filter(id__in=event_ids).select_related("actor").order_by("created_at")
    details = []
    for event in events:
        details.append({
            "id": event.id,
            "created_at": event.created_at,
            "event_type": event.event_type,
            "actor": getattr(event.actor, "email", None),
            "severity": event.severity,
            "risk_score": event.risk_score,
            "metadata": event.metadata or {},
        })
    return details


def summarize_incident(events: List[Dict[str, object]]) -> str:
    if not events:
        return "No related security events were found."
    types = {}
    actors = set()
    max_risk = 0.0
    for event in events:
        event_type = str(event.get("event_type", "unknown"))
        types[event_type] = types.get(event_type, 0) + 1
        actor = event.get("actor")
        if actor:
            actors.add(str(actor))
        max_risk = max(max_risk, float(event.get("risk_score", 0.0) or 0.0))
    parts = [f"{count} {event_type.replace('_', ' ')} event(s)" for event_type, count in types.items()]
    summary = "Incident summary: " + ", ".join(parts) + "."
    if actors:
        summary += " Affected accounts: " + ", ".join(sorted(actors)) + "."
    summary += f" Maximum risk score: {max_risk:.1f}."
    summary += " Review the linked events and affected accounts before taking action."
    return summary


def create_incident_for_security_event(event) -> "SecurityIncident":
    from audit.models import SecurityEvent
    from .models import SecurityIncident

    if isinstance(event, SecurityEvent):
        security_event = event
    else:
        security_event = None
    event_data = {
        "event_type": getattr(security_event, "event_type", "unknown"),
        "actor": getattr(getattr(security_event, "actor", None), "email", None),
        "risk_score": getattr(security_event, "risk_score", 0.0),
    }
    incident = SecurityIncident.objects.create(
        title=f"Security incident: {event_data['event_type'].replace('_', ' ')}",
        severity=getattr(security_event, "severity", "medium") if security_event else "medium",
        status="new",
        summary=summarize_incident([event_data]),
        related_events=[security_event.id] if security_event else [],
        history=[{"action": "created", "at": timezone.now().isoformat()}],
    )
    return incident