from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import PatientProfile, User
from .forms import LabRequestForm, ReportUploadForm
from .models import LabReport, LabTestRequest
from .services import create_lab_request, decrypt_report, download_document, reject_report, upload_report


@login_required
def lab_requests_view(request):
    user = request.user
    if user.is_doctor():
        requests = LabTestRequest.objects.filter(doctor=user).order_by("-created_at")
    elif user.is_lab_tech():
        requests = LabTestRequest.objects.filter(assigned_technician=user).order_by("-created_at")
    elif user.is_patient():
        requests = LabTestRequest.objects.filter(patient=user.patient_profile).order_by("-created_at")
    else:
        requests = LabTestRequest.objects.all().order_by("-created_at")[:100]
    return render(request, "laboratory/requests.html", {"requests": requests})


@login_required
def create_request_view(request):
    user = request.user
    if not (user.is_doctor() or user.is_administrator()):
        return render(request, "errors/403.html", status=403)
    if request.method == "POST":
        form = LabRequestForm(request.POST)
        if form.is_valid():
            patient = get_object_or_404(PatientProfile, id=form.cleaned_data["patient_id"])
            technician = None
            if form.cleaned_data.get("technician_id"):
                technician = get_object_or_404(User, id=form.cleaned_data["technician_id"], role="lab_tech")
            try:
                lr = create_lab_request(user, patient, form.cleaned_data["test_type"], form.cleaned_data["priority"], form.cleaned_data.get("notes", ""), technician, request=request)
                messages.success(request, "Lab request created.")
                return redirect("laboratory:requests")
            except PermissionError as exc:
                messages.error(request, str(exc))
    else:
        form = LabRequestForm()
    patients = PatientProfile.objects.all()
    technicians = User.objects.filter(role="lab_tech", is_active=True)
    return render(request, "laboratory/create_request.html", {"form": form, "patients": patients, "technicians": technicians})


@login_required
def upload_report_view(request):
    user = request.user
    if not (user.is_lab_tech() or user.is_administrator()):
        return render(request, "errors/403.html", status=403)
    if request.method == "POST":
        form = ReportUploadForm(request.POST, request.FILES)
        if form.is_valid():
            lr = get_object_or_404(LabTestRequest, id=form.cleaned_data["request_id"])
            try:
                report, doc = upload_report(user, lr, request.FILES["file"], form.cleaned_data.get("result_text", ""), request=request)
                messages.success(request, "Encrypted report uploaded.")
                return redirect("laboratory:reports")
            except (PermissionError, ValueError) as exc:
                messages.error(request, str(exc))
    else:
        form = ReportUploadForm()
    requests = LabTestRequest.objects.filter(status__in=["requested", "in_progress"])
    if user.is_lab_tech():
        requests = requests.filter(assigned_technician=user)
    return render(request, "laboratory/upload_report.html", {"form": form, "requests": requests})


@login_required
def reports_view(request):
    user = request.user
    if user.is_patient():
        reports = LabReport.objects.filter(request__patient=user.patient_profile).order_by("-created_at")
    elif user.is_doctor():
        reports = LabReport.objects.filter(request__doctor=user).order_by("-created_at")
    elif user.is_lab_tech():
        reports = LabReport.objects.filter(technician=user).order_by("-created_at")
    else:
        reports = LabReport.objects.all().order_by("-created_at")[:100]
    from security.models import EncryptedDocument
    rows = []
    for rep in reports:
        try:
            result_text = decrypt_report(user, rep)
        except Exception:
            result_text = ""
        doc = EncryptedDocument.objects.filter(related_type="LabTestRequest", related_id=rep.request.id).order_by("-created_at").first()
        rows.append({"report": rep, "result_text": result_text, "document": doc})
    return render(request, "laboratory/reports.html", {"rows": rows})


@login_required
def download_report_view(request, document_id):
    from security.models import EncryptedDocument

    doc = get_object_or_404(EncryptedDocument, id=document_id)
    user = request.user
    try:
        raw, document = download_document(user, doc)
    except PermissionError:
        return render(request, "errors/403.html", status=403)
    except Exception:
        messages.error(request, "Unable to decrypt document.")
        return redirect("laboratory:reports")
    response = HttpResponse(raw, content_type=document.content_type or "application/octet-stream")
    response["Content-Disposition"] = f'attachment; filename="{document.original_filename}"'
    return response


@login_required
def reject_report_view(request, report_id):
    report = get_object_or_404(LabReport, id=report_id)
    user = request.user
    try:
        reject_report(user, report)
        messages.success(request, "Report rejected.")
    except PermissionError as exc:
        messages.error(request, str(exc))
    return redirect("laboratory:reports")
