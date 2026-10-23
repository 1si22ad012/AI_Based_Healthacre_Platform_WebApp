import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import PatientProfile
from accounts.permissions import can_access_patient
from .forms import PrescriptionForm
from .models import Prescription
from .services import create_prescription, decrypt_prescription, verify_prescription_signature


@login_required
def prescriptions_view(request):
    user = request.user
    if user.is_patient():
        prescriptions = Prescription.objects.filter(patient=user.patient_profile).order_by("-created_at")
    elif user.is_doctor():
        prescriptions = Prescription.objects.filter(doctor=user).order_by("-created_at")
    else:
        prescriptions = Prescription.objects.all().order_by("-created_at")[:100]
    data = []
    for rx in prescriptions:
        try:
            payload = decrypt_prescription(user, rx)
        except Exception:
            payload = {}
        data.append((rx, payload, verify_prescription_signature(rx, payload) if payload else False))
    return render(request, "prescriptions/list.html", {"items": data})


@login_required
def create_prescription_view(request):
    user = request.user
    if not (user.is_doctor() or user.is_administrator()):
        return render(request, "errors/403.html", status=403)
    if request.method == "POST":
        form = PrescriptionForm(request.POST)
        if form.is_valid():
            patient = get_object_or_404(PatientProfile, id=form.cleaned_data["patient_id"])
            payload = {
                "clinical_notes": form.cleaned_data.get("clinical_notes", ""),
                "medication": form.cleaned_data["medication_name"],
            }
            items = [{
                "medication_name": form.cleaned_data["medication_name"],
                "dosage": form.cleaned_data["dosage"],
                "frequency": form.cleaned_data["frequency"],
                "duration": form.cleaned_data.get("duration", ""),
                "instructions": form.cleaned_data.get("instructions", ""),
            }]
            try:
                rx, _ = create_prescription(user, patient, form.cleaned_data["title"], payload, items=items, request=request, sign=True)
                messages.success(request, "Prescription created and signed.")
                return redirect("prescriptions:list")
            except PermissionError as exc:
                messages.error(request, str(exc))
    else:
        form = PrescriptionForm()
    patients = PatientProfile.objects.all()
    return render(request, "prescriptions/create.html", {"form": form, "patients": patients})


@login_required
def view_prescription_view(request, prescription_id):
    rx = get_object_or_404(Prescription, id=prescription_id)
    user = request.user
    try:
        payload = decrypt_prescription(user, rx)
    except PermissionError:
        return render(request, "errors/403.html", status=403)
    except Exception:
        messages.error(request, "Unable to decrypt prescription.")
        return redirect("prescriptions:list")
    valid = verify_prescription_signature(rx, payload)
    return render(request, "prescriptions/view.html", {"rx": rx, "payload": payload, "valid_signature": valid})
