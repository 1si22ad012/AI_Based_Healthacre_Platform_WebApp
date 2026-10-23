from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import PatientProfile
from accounts.permissions import can_access_patient, is_doctor
from audit.services import create_audit_event
from .forms import DiagnosisForm, MedicalRecordForm
from .models import MedicalRecord
from .services import create_diagnosis, decrypt_medical_record, encrypt_medical_record


@login_required
def patient_records_view(request):
    user = request.user
    if user.is_patient():
        patients = [user.patient_profile]
    elif user.is_doctor() or user.is_administrator():
        # Doctors see patients they are authorized for; admins operational list limited.
        patients = PatientProfile.objects.all()[:50]
    else:
        patients = []
    selected_patient = None
    pid = request.GET.get("patient")
    if pid:
        selected_patient = get_object_or_404(PatientProfile, id=pid)
        if not can_access_patient(user, selected_patient):
            return render(request, "errors/403.html", status=403)
    records = []
    if selected_patient:
        records = MedicalRecord.objects.filter(patient=selected_patient, is_deleted=False).order_by("-created_at")
    return render(request, "patients/records.html", {"patients": patients, "selected_patient": selected_patient, "records": records})


@login_required
def create_record_view(request):
    user = request.user
    if request.method == "POST":
        form = MedicalRecordForm(request.POST)
        if form.is_valid():
            patient = get_object_or_404(PatientProfile, id=form.cleaned_data["patient_id"])
            try:
                record, policy = encrypt_medical_record(
                    user, patient, form.cleaned_data["title"], form.cleaned_data["content"],
                    form.cleaned_data["sensitivity"], request=request,
                )
                messages.success(request, f"Record encrypted using {policy['algorithm']} ({policy['policy']}).")
                return redirect(f"/patients/records/?patient={patient.id}")
            except PermissionError as exc:
                messages.error(request, str(exc))
    else:
        form = MedicalRecordForm()
    patients = PatientProfile.objects.all() if user.is_doctor() or user.is_administrator() else [user.patient_profile]
    return render(request, "patients/create_record.html", {"form": form, "patients": patients})


@login_required
def view_record_view(request, record_id):
    record = get_object_or_404(MedicalRecord, id=record_id, is_deleted=False)
    user = request.user
    try:
        plaintext, _ = decrypt_medical_record(user, record, request=request)
    except PermissionError:
        return render(request, "errors/403.html", status=403)
    except Exception:
        messages.error(request, "Unable to decrypt record.")
        return redirect("patients:records")
    create_audit_event("record.view", actor=user, target_type="MedicalRecord", target_id=record.id, request=request, result="success")
    return render(request, "patients/view_record.html", {"record": record, "plaintext": plaintext})


@login_required
def create_diagnosis_view(request):
    user = request.user
    if not (user.is_doctor() or user.is_administrator()):
        return render(request, "errors/403.html", status=403)
    if request.method == "POST":
        form = DiagnosisForm(request.POST)
        if form.is_valid():
            patient = get_object_or_404(PatientProfile, id=form.cleaned_data["patient_id"])
            try:
                diagnosis = create_diagnosis(user, patient, form.cleaned_data["title"], form.cleaned_data["notes"], request=request)
                messages.success(request, "Diagnosis saved and encrypted.")
                return redirect(f"/patients/records/?patient={patient.id}")
            except PermissionError as exc:
                messages.error(request, str(exc))
    else:
        form = DiagnosisForm()
    patients = PatientProfile.objects.all()
    return render(request, "patients/create_diagnosis.html", {"form": form, "patients": patients})
