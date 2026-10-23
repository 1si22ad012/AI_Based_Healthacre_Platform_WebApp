from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import PatientProfile, User
from accounts.permissions import can_access_patient
from .forms import AppointmentForm
from .models import Appointment, AppointmentStatus
from .services import create_appointment, decrypt_appointment_notes


@login_required
def appointments_view(request):
    user = request.user
    if user.is_patient():
        appointments = Appointment.objects.filter(patient=user.patient_profile).order_by("scheduled_at")
    elif user.is_doctor():
        appointments = Appointment.objects.filter(doctor=user).order_by("scheduled_at")
    elif user.is_lab_tech():
        appointments = Appointment.objects.none()
    else:
        appointments = Appointment.objects.all().order_by("scheduled_at")[:100]
    rows = []
    for appt in appointments:
        try:
            note = decrypt_appointment_notes(user, appt)
        except Exception:
            note = ""
        rows.append({"appointment": appt, "note": note})
    return render(request, "appointments/list.html", {
        "rows": rows,
        "status_choices": AppointmentStatus.choices,
    })


@login_required
def create_appointment_view(request):
    user = request.user
    if request.method == "POST":
        form = AppointmentForm(request.POST)
        if form.is_valid():
            patient = get_object_or_404(PatientProfile, id=form.cleaned_data["patient_id"])
            doctor = None
            if form.cleaned_data.get("doctor_id"):
                doctor = get_object_or_404(User, id=form.cleaned_data["doctor_id"], role="doctor")
            try:
                appointment = create_appointment(
                    user, patient, form.cleaned_data["scheduled_at"],
                    form.cleaned_data.get("reason", ""), form.cleaned_data.get("notes", ""),
                    doctor=doctor, request=request,
                )
                messages.success(request, "Appointment created.")
                return redirect("appointments:list")
            except PermissionError as exc:
                messages.error(request, str(exc))
    else:
        form = AppointmentForm()
    patients = PatientProfile.objects.all() if not user.is_patient() else [user.patient_profile]
    doctors = User.objects.filter(role="doctor", is_active=True)
    return render(request, "appointments/create.html", {"form": form, "patients": patients, "doctors": doctors})


@login_required
def update_status_view(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    user = request.user
    if not (user.is_doctor() or user.is_administrator() or (user.is_patient() and appointment.patient.user == user)):
        return render(request, "errors/403.html", status=403)
    if request.method == "POST":
        status_value = request.POST.get("status")
        if status_value in dict(AppointmentStatus.choices):
            appointment.status = status_value
            appointment.save(update_fields=["status", "updated_at"])
            messages.success(request, "Appointment status updated.")
    return redirect("appointments:list")
