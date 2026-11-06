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


def _symptom_text(data) -> str:
    if isinstance(data, str):
        return data
    if isinstance(data, dict):
        parts = [data.get("symptoms", ""), data.get("additional_symptoms", ""), data.get("medical_history", "")]
        return " ".join(str(p) for p in parts if p)
    return str(data)


def analyze_symptoms(data) -> Dict[str, object]:
    text = _normalize(_symptom_text(data))
    structured = data if isinstance(data, dict) else {"symptoms": data}
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

    missing = []
    if not structured.get("duration"):
        missing.append("duration")
    if not structured.get("severity"):
        missing.append("severity")

    if emergency:
        urgency = "emergency"
    elif structured.get("severity", "").lower() in ("severe", "high"):
        urgency = "urgent"
    else:
        urgency = "routine"

    # Retrieve trusted guidance
    try:
        from .rag import retrieve

        guidance = retrieve(text, top_k=2)
    except Exception:
        guidance = []

    explanation = (
        "Symptoms were matched to possible specialties using a transparent keyword-based classifier. "
        "This is preliminary navigation only and not a diagnosis."
    )
    if emergency:
        explanation += " Emergency symptoms may be present; seek immediate medical care."
    if guidance:
        explanation += " Related trusted information: " + "; ".join(g["chunk_text"] for g in guidance)
    if missing:
        explanation += " Missing information: " + ", ".join(missing) + "."

    return {
        "specialties": specialties,
        "emergency": emergency,
        "recommended_urgency": urgency,
        "missing_info": missing,
        "explanation": explanation,
        "guidance": guidance,
    }


def recommend_doctors(specialties: List[str]):
    names = [name.strip() for name in specialties]
    return DoctorProfile.objects.filter(
        specialization__name__in=names,
        user__is_active=True,
        user__approval_status="approved",
    ).select_related("user", "specialization")


EMERGENCY_KEYWORDS_CHAT = ["chest pain", "difficulty breathing", "shortness of breath", "unconscious", "seizure", "stroke", "severe bleeding", "loss of consciousness", "suicidal"]


def _rule_based_chatbot(message: str) -> str:
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


def chatbot_response(message: str, user=None) -> str:
    return _rule_based_chatbot(message)


def _safety_filter(text: str) -> str:
    if not text:
        return text
    lowered = text.lower()
    unsafe_phrases = ["you have", "diagnosis is", "take this medication", "stop taking", "dosage of"]
    for phrase in unsafe_phrases:
        if phrase in lowered:
            return (
                "I can provide general health information only. I cannot diagnose conditions or prescribe treatment. "
                "Please consult a qualified healthcare professional."
            )
    return text


def chatbot_answer(message: str, user=None, conversation=None):
    """Return (response_text, sources_list, conversation). Uses LLM+RAG when configured, else safe fallback."""
    from .models import ChatConversation, ChatMessage
    from .rag import retrieve
    from .llm import call_llm, llm_configured, SAFETY_SYSTEM_PROMPT

    message = (message or "").strip()
    if not message:
        return "Please enter a message.", [], conversation

    if conversation is None:
        conversation = ChatConversation.objects.create(user=user, title=message[:80])

    ChatMessage.objects.create(conversation=conversation, role="user", content=message)

    # Emergency detection
    lowered = _normalize(message)
    is_emergency = any(k in lowered for k in EMERGENCY_KEYWORDS_CHAT)

    sources = retrieve(message)
    context_block = ""
    if sources:
        context_block = "\n\nRelevant trusted sources:\n" + "\n".join(
            f"- {s['source_title']}: {s['chunk_text']}" for s in sources
        )

    if llm_configured():
        history_msgs = [{"role": "system", "content": SAFETY_SYSTEM_PROMPT}]
        recent = list(conversation.messages.order_by("-created_at")[:6])
        recent.reverse()
        for m in recent:
            if m.role in ("user", "assistant"):
                history_msgs.append({"role": m.role, "content": m.content})
        user_content = message
        if context_block:
            user_content += context_block
        if is_emergency:
            user_content += "\n\nNote: The user may be describing an emergency. Prioritize advising immediate emergency services."
        history_msgs.append({"role": "user", "content": user_content})
        text, err = call_llm(history_msgs)
        if text:
            text = _safety_filter(text)
            if is_emergency and "emergency" not in text.lower():
                text = "If this may be a medical emergency, contact local emergency services immediately. " + text
            if sources:
                refs = "\n\nSources: " + ", ".join(s["source_title"] for s in sources)
                text = text + refs
        else:
            text = _rule_based_chatbot(message)
            if is_emergency:
                text = "If this may be a medical emergency, contact local emergency services immediately. " + text
    else:
        text = _rule_based_chatbot(message)
        if is_emergency:
            text = "If this may be a medical emergency, contact local emergency services immediately. " + text
        if sources:
            text = text + "\n\nRelated information: " + "; ".join(s["chunk_text"] for s in sources[:2])

    ChatMessage.objects.create(conversation=conversation, role="assistant", content=text, sources=sources)
    conversation.save(update_fields=["updated_at"])
    return text, sources, conversation


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