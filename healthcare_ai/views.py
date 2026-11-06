from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from accounts.models import DoctorProfile, Specialization
from accounts.permissions import is_admin as is_administrator
import json

from .models import AIConversation, FaceVerificationRecord, SecurityIncident, SymptomAssessment
from .services import analyze_symptoms, calculate_risk_score, chatbot_response, explain_risk, incident_events, recommend_doctors, summarize_incident
from .voice import resolve_voice_command
from .risk_history import top_risk_accounts


@login_required
def doctor_search_view(request):
    query = request.GET.get("q", "").strip()
    specialty_id = request.GET.get("specialty", "").strip()
    doctors = DoctorProfile.objects.filter(user__is_active=True, user__approval_status="approved").select_related("user", "specialization")
    if query:
        doctors = doctors.filter(user__first_name__icontains=query) | doctors.filter(user__last_name__icontains=query) | doctors.filter(specialization__name__icontains=query)
    if specialty_id:
        doctors = doctors.filter(specialization_id=specialty_id)
    specialties = Specialization.objects.filter(is_active=True).order_by("name")
    return render(request, "healthcare_ai/doctor_search.html", {"doctors": doctors, "specialties": specialties, "query": query, "specialty_id": specialty_id})


@login_required
def symptom_assessment_view(request):
    result = None
    recommended_doctors = []
    if request.method == "POST":
        data = {
            "symptoms": request.POST.get("symptoms", "").strip(),
            "additional_symptoms": request.POST.get("additional_symptoms", "").strip(),
            "duration": request.POST.get("duration", "").strip(),
            "severity": request.POST.get("severity", "").strip(),
            "onset": request.POST.get("onset", "").strip(),
            "frequency": request.POST.get("frequency", "").strip(),
            "trend": request.POST.get("trend", "").strip(),
            "medical_history": request.POST.get("medical_history", "").strip(),
            "medications": request.POST.get("medications", "").strip(),
            "allergies": request.POST.get("allergies", "").strip(),
            "age_range": request.POST.get("age_range", "").strip(),
        }
        if not data["symptoms"]:
            messages.error(request, "Please enter symptoms.")
        else:
            analysis = analyze_symptoms(data)
            assessment = SymptomAssessment.objects.create(
                patient=request.user,
                symptoms=data["symptoms"],
                duration=data["duration"],
                severity=data["severity"],
                onset=data["onset"],
                frequency=data["frequency"],
                trend=data["trend"],
                medical_history=data["medical_history"],
                medications=data["medications"],
                allergies=data["allergies"],
                age_range=data["age_range"],
                predicted_specialties=analysis["specialties"],
                emergency=analysis["emergency"],
                recommended_urgency=analysis["recommended_urgency"],
                missing_info=analysis["missing_info"],
                explanation=analysis["explanation"],
            )
            recommended_doctors = list(recommend_doctors(analysis["specialties"]))
            if analysis["emergency"]:
                messages.error(request, "Emergency symptoms may be present. Seek immediate medical care or call local emergency services.")
            else:
                messages.success(request, "Symptom assessment completed. This is not a diagnosis.")
            result = {"assessment": assessment, "analysis": analysis}
    return render(request, "healthcare_ai/symptom_assessment.html", {"result": result, "recommended_doctors": recommended_doctors})


@login_required
def chatbot_view(request):
    from .models import ChatConversation, ChatMessage
    from .services import chatbot_answer

    conversation_id = request.POST.get("conversation_id") or request.GET.get("conversation")
    conversation = None
    if conversation_id:
        conversation = ChatConversation.objects.filter(id=conversation_id, user=request.user).first()

    if request.method == "POST":
        message = request.POST.get("message", "").strip()
        if message:
            response, sources, conversation = chatbot_answer(message, request.user, conversation)
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"response": response, "sources": sources, "conversation_id": conversation.id})
            messages.success(request, "Assistant response generated.")

    conversations = ChatConversation.objects.filter(user=request.user).prefetch_related("messages")
    active_messages = conversation.messages.all() if conversation else []
    return render(request, "healthcare_ai/chatbot.html", {
        "conversations": conversations,
        "active_conversation": conversation,
        "active_messages": active_messages,
    })


@login_required
def security_incidents_view(request):
    if not is_administrator(request.user):
        return render(request, "errors/403.html", status=403)
    incidents = SecurityIncident.objects.all()
    if request.method == "POST":
        incident_id = request.POST.get("incident_id")
        action = request.POST.get("action")
        incident = SecurityIncident.objects.filter(id=incident_id).first()
        if incident:
            if action == "acknowledge":
                incident.status = "acknowledged"
            elif action == "investigate":
                incident.status = "under_investigation"
            elif action == "resolve":
                incident.status = "resolved"
                from django.utils import timezone
                incident.resolved_at = timezone.now()
            elif action == "false_positive":
                incident.status = "false_positive"
            incident.assigned_to = request.user
            incident.save(update_fields=["status", "assigned_to", "resolved_at", "updated_at"])
            messages.success(request, "Incident updated.")
            return redirect("healthcare_ai:security_incidents")
    return render(request, "healthcare_ai/security_incidents.html", {"incidents": incidents})


@login_required
def face_verification_view(request):
    record, _ = FaceVerificationRecord.objects.get_or_create(user=request.user)
    if request.method == "POST":
        if request.POST.get("consent") == "on":
            record.consent_given = True
            record.enrolled = True
            record.enrolled_at = timezone.now()
            record.template_hash = request.POST.get("template_hash", "")[:128]
            record.save(update_fields=["consent_given", "enrolled", "enrolled_at", "template_hash"])
            messages.success(request, "Face verification enrollment recorded. Password login remains available.")
        elif request.POST.get("action") == "remove":
            record.enrolled = False
            record.consent_given = False
            record.template_hash = ""
            record.save(update_fields=["enrolled", "consent_given", "template_hash"])
            messages.success(request, "Face verification enrollment removed.")
        return redirect("healthcare_ai:face_verification")
    return render(request, "healthcare_ai/face_verification.html", {"record": record})


@login_required
def voice_command_view(request):
    if request.method != "POST":
        return JsonResponse({"action": "none", "message": "Voice command endpoint."}, status=405)
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        payload = {}
    transcript = payload.get("transcript", request.POST.get("transcript", ""))
    result = resolve_voice_command(transcript, getattr(request.user, "role", ""))
    return JsonResponse(result)


@login_required
def risk_analysis_view(request):
    if not is_administrator(request.user):
        return render(request, "errors/403.html", status=403)
    result = None
    if request.method == "POST":
        features = {
            "failed_logins": int(request.POST.get("failed_logins", 0) or 0),
            "denied_requests": int(request.POST.get("denied_requests", 0) or 0),
            "invalid_tags": int(request.POST.get("invalid_tags", 0) or 0),
            "unusual_hour": request.POST.get("unusual_hour") == "on",
            "anomaly": request.POST.get("anomaly") == "on",
        }
        risk = calculate_risk_score(features)
        result = {"features": features, "risk": risk, "explanation": explain_risk(features)}
    return render(request, "healthcare_ai/risk_analysis.html", {"result": result})


@login_required
def risk_dashboard_view(request):
    if not is_administrator(request.user):
        return render(request, "errors/403.html", status=403)
    days = int(request.GET.get("days", 30) or 30)
    accounts = top_risk_accounts(limit=15, days=days)
    return render(request, "healthcare_ai/risk_dashboard.html", {"accounts": accounts, "days": days})


@login_required
def incident_summary_view(request, incident_id):
    if not is_administrator(request.user):
        return render(request, "errors/403.html", status=403)
    incident = SecurityIncident.objects.filter(id=incident_id).first()
    if not incident:
        return render(request, "errors/404.html", status=404)
    events = incident_events(incident)
    summary = incident.summary or summarize_incident(events)
    return render(request, "healthcare_ai/incident_summary.html", {"incident": incident, "summary": summary, "events": events})