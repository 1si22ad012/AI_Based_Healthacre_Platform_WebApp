from django.contrib import messages
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods



from audit.services import create_audit_event, create_security_event
from django.utils import timezone
from healthcare_ai.services import calculate_risk_score, explain_risk
from healthcare_ai.models import LoginAudit
from .forms import AdminUserForm, ProfileForm, RegistrationForm
from .models import ApprovalStatus, DoctorProfile, PatientProfile, Role, Specialization, User
from .permissions import is_admin


def login_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    ip = request.META.get("REMOTE_ADDR", "unknown")
    cache_key = f"login-attempts:{ip}"
    attempts = cache.get(cache_key, 0)
    if attempts >= 10:
        messages.error(request, "Too many login attempts. Please try again later.")
        return render(request, "accounts/login.html")
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        candidate = User.objects.filter(email=email).first()
        if candidate and not candidate.is_active and candidate.check_password(password):
            if candidate.approval_status == ApprovalStatus.PENDING:
                messages.error(request, "Your account is pending administrator approval.")
            else:
                messages.error(request, "Your account is inactive.")
            return render(request, "accounts/login.html")
        user = authenticate(request, username=email, password=password)
        if user is not None and user.is_active:
            login(request, user)
            cache.delete(cache_key)
            user_agent = request.META.get("HTTP_USER_AGENT", "")[:500]
            risk = calculate_risk_score({
                "failed_logins": user.failed_login_count,
                "unusual_hour": timezone.now().hour < 6 or timezone.now().hour > 22,
            })
            login_audit = LoginAudit.objects.create(
                user=user,
                ip_address=request.META.get("REMOTE_ADDR"),
                user_agent=user_agent,
                risk_score=risk["score"],
                risk_level=risk["level"],
            )
            try:
                send_mail(
                    subject="New login to your healthcare account",
                    message=(
                        f"Hello {user.full_name},\n\n"
                        f"A login was recorded at {login_audit.login_at}.\n"
                        f"IP address: {login_audit.ip_address or 'unknown'}\n"
                        f"Device/browser: {user_agent or 'unknown'}\n\n"
                        "If this was not you, report it immediately and change your password.\n"
                    ),
                    from_email=None,
                    recipient_list=[user.email],
                    fail_silently=True,
                )
                login_audit.email_sent = True
                login_audit.save(update_fields=["email_sent"])
            except Exception:
                pass
            create_security_event("login_success", actor=user, request=request, severity="info", risk_score=risk["score"])
            create_audit_event("auth.login", actor=user, request=request, result="success", details={"risk_level": risk["level"], "reasons": risk["reasons"]})
            if risk["score"] >= 60:
                create_security_event("anomaly", actor=user, request=request, metadata={"reason": "suspicious_login", "risk": risk}, severity="high", risk_score=risk["score"])
            messages.success(request, "Welcome back.")
            return redirect("accounts:dashboard")
        cache.set(cache_key, attempts + 1, timeout=900)
        create_security_event("login_failure", actor=None, request=request, metadata={"email": email}, severity="medium", risk_score=0.3)
        messages.error(request, "Invalid email or password.")
    return render(request, "accounts/login.html")


def logout_view(request):
    if request.user.is_authenticated:
        create_security_event("logout", actor=request.user, request=request)
        create_audit_event("auth.logout", actor=request.user, request=request, result="success")
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("accounts:login")


def register_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            create_audit_event("auth.register", actor=user, request=request, result="success", details={"role": user.role, "approval_status": user.approval_status})
            if user.approval_status == ApprovalStatus.APPROVED:
                login(request, user)
                create_security_event("login_success", actor=user, request=request, metadata={"registration": True})
                messages.success(request, "Account created successfully.")
                return redirect("accounts:dashboard")
            messages.success(request, "Registration submitted. Your professional account is pending administrator approval.")
            from audit.services import notify_user
            from .models import User

            for admin_user in User.objects.filter(role=Role.ADMIN) | User.objects.filter(is_superuser=True):
                notify_user(admin_user, "New professional registration", f"{user.email} registered as {user.role} and requires approval.", category="admin", url="/users/")
            return redirect("accounts:login")
    else:
        form = RegistrationForm()
    return render(request, "accounts/register.html", {"form": form})


@login_required
def password_change_view(request):
    if request.method == "POST":
        old_password = request.POST.get("old_password", "")
        new_password = request.POST.get("new_password", "")
        confirm = request.POST.get("confirm_password", "")
        if not request.user.check_password(old_password):
            messages.error(request, "Current password is incorrect.")
        elif len(new_password) < 10:
            messages.error(request, "New password must be at least 10 characters.")
        elif new_password != confirm:
            messages.error(request, "New passwords do not match.")
        else:
            request.user.set_password(new_password)
            request.user.save(update_fields=["password"])
            update_session_auth_hash(request, request.user)
            create_audit_event("auth.password_change", actor=request.user, request=request, result="success")
            messages.success(request, "Password changed successfully.")
            return redirect("accounts:profile")
    return render(request, "accounts/password_change.html")


@login_required
def profile_view(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            create_audit_event("profile.update", actor=request.user, request=request, result="success")
            messages.success(request, "Profile updated.")
            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=request.user)
    return render(request, "accounts/profile.html", {"form": form})


def _normalize_role(user):
    role = str(getattr(user, "role", "") or "").strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "laboratorytechnician": "lab_tech",
        "labtechnician": "lab_tech",
        "labtech": "lab_tech",
        "administrator": "admin",
    }
    return aliases.get(role, role)


def dashboard_router(request):
    if not request.user.is_authenticated:
        return render(request, "accounts/landing.html")
    from appointments.models import Appointment
    from prescriptions.models import Prescription
    from laboratory.models import LabTestRequest, LabReport
    from patients.models import MedicalRecord
    from security.models import EncryptionOperation, KeyMetadata
    from audit.models import SecurityEvent, AnomalyAlert, AuditEvent
    from django.db.models import Count

    user = request.user
    role = _normalize_role(user)

    if role == Role.PATIENT:
        from .models import PatientProfile

        pp, _ = PatientProfile.objects.get_or_create(user=user)
        context = {
            "appointments_count": Appointment.objects.filter(patient=pp).count(),
            "prescriptions_count": Prescription.objects.filter(patient=pp).count(),
            "reports_count": LabReport.objects.filter(request__patient=pp).count(),
            "records_count": MedicalRecord.objects.filter(patient=pp, is_deleted=False).count(),
            "notifications_count": user.notifications.filter(is_read=False).count(),
        }
        return render(request, "accounts/dashboard_patient.html", context)
    if role == Role.DOCTOR:
        from .models import DoctorProfile

        DoctorProfile.objects.get_or_create(user=user)
        context = {
            "appointments_count": Appointment.objects.filter(doctor=user).count(),
            "pending_labs": LabTestRequest.objects.filter(doctor=user, status="requested").count(),
            "prescriptions_count": Prescription.objects.filter(doctor=user).count(),
            "records_count": MedicalRecord.objects.filter(created_by=user).count(),
        }
        from accounts.models import PatientProfile

        patient_ids = set(Appointment.objects.filter(doctor=user).values_list("patient_id", flat=True))
        patient_ids.update(Prescription.objects.filter(doctor=user).values_list("patient_id", flat=True))
        patient_ids.update(MedicalRecord.objects.filter(created_by=user).values_list("patient_id", flat=True))
        patient_ids.update(LabTestRequest.objects.filter(doctor=user).values_list("patient_id", flat=True))
        context["patients_count"] = PatientProfile.objects.filter(id__in=patient_ids).count()
        return render(request, "accounts/dashboard_doctor.html", context)
    if role == Role.LAB_TECH:
        from .models import LabTechProfile

        LabTechProfile.objects.get_or_create(user=user)
        context = {
            "pending_requests": LabTestRequest.objects.filter(assigned_technician=user, status__in=["requested", "in_progress"]).count(),
            "completed_tests": LabTestRequest.objects.filter(assigned_technician=user, status="completed").count(),
            "reports_uploaded": LabReport.objects.filter(technician=user).count(),
            "all_pending": LabTestRequest.objects.filter(status__in=["requested", "in_progress"]).count(),
        }
        return render(request, "accounts/dashboard_lab.html", context)
    if role == Role.ADMIN or user.is_superuser:
        users_by_role = User.objects.values("role").annotate(count=Count("id"))
        role_counts = {r["role"]: r["count"] for r in users_by_role}
        context = {
            "total_users": User.objects.count(),
            "active_users": User.objects.filter(is_active=True).count(),
            "suspended_users": User.objects.filter(is_active=False).count(),
            "role_counts": role_counts,
            "appointments_total": Appointment.objects.count(),
            "pending_labs": LabTestRequest.objects.filter(status__in=["requested", "in_progress"]).count(),
            "recent_security_events": SecurityEvent.objects.count(),
            "open_alerts": AnomalyAlert.objects.filter(status="open").count(),
            "encryption_ops": EncryptionOperation.objects.count(),
            "encryption_failures": EncryptionOperation.objects.filter(success=False).count(),
            "keys": KeyMetadata.objects.all()[:5],
            "recent_audit": AuditEvent.objects.all()[:10],
            "recent_events": SecurityEvent.objects.all()[:10],
        }
        return render(request, "accounts/dashboard_admin.html", context)
    messages.error(request, "Your account role is not supported.")
    return render(request, "errors/403.html", status=403)

@login_required
def user_management_view(request):
    if not is_admin(request.user):
        return render(request, "errors/403.html", status=403)
    if request.method == "POST":
        form = AdminUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password("ChangeMe123!Secure")
            user.save()
            from .models import PatientProfile, DoctorProfile, LabTechProfile

            if user.role == "patient":
                PatientProfile.objects.get_or_create(user=user)
            elif user.role == "doctor":
                DoctorProfile.objects.get_or_create(user=user)
            elif user.role == "lab_tech":
                LabTechProfile.objects.get_or_create(user=user)
            create_audit_event("admin.create_user", actor=request.user, target_type="User", target_id=user.id, request=request, result="success")
            messages.success(request, f"Created {user.email} with temporary password ChangeMe123!Secure.")
            return redirect("accounts:user_management")
    else:
        form = AdminUserForm()
    users = User.objects.all().order_by("-date_joined")
    pending_professionals = User.objects.filter(role__in=[Role.DOCTOR, Role.LAB_TECH], approval_status=ApprovalStatus.PENDING).order_by("-date_joined")
    return render(request, "accounts/user_management.html", {"users": users, "form": form, "pending_professionals": pending_professionals})


@login_required
@require_http_methods(["POST"])
def approve_user_view(request, user_id):
    if not is_admin(request.user):
        return render(request, "errors/403.html", status=403)
    target = get_object_or_404(User, id=user_id)
    if target.role not in {Role.DOCTOR, Role.LAB_TECH}:
        messages.error(request, "Only professional registrations can be approved.")
        return redirect("accounts:user_management")
    target.is_active = True
    target.approval_status = ApprovalStatus.APPROVED
    target.approved_by = request.user
    target.approved_at = timezone.now()
    target.save(update_fields=["is_active", "approval_status", "approved_by", "approved_at"])
    from .models import DoctorProfile, LabTechProfile, PatientProfile

    if target.role == Role.DOCTOR:
        DoctorProfile.objects.get_or_create(user=target)
    elif target.role == Role.LAB_TECH:
        LabTechProfile.objects.get_or_create(user=target)
    create_audit_event("admin.approve_user", actor=request.user, target_type="User", target_id=target.id, request=request, result="success", details={"role": target.role})
    from audit.services import notify_user

    notify_user(target, "Account approved", "Your professional account has been approved. You can now log in.", category="account", url="/login/")
    messages.success(request, f"Approved {target.email}.")
    return redirect("accounts:user_management")


@login_required
@require_http_methods(["POST"])
def reject_user_view(request, user_id):
    if not is_admin(request.user):
        return render(request, "errors/403.html", status=403)
    target = get_object_or_404(User, id=user_id)
    if target.role not in {Role.DOCTOR, Role.LAB_TECH}:
        messages.error(request, "Only professional registrations can be rejected.")
        return redirect("accounts:user_management")
    target.is_active = False
    target.approval_status = ApprovalStatus.REJECTED
    target.approved_by = request.user
    target.approved_at = timezone.now()
    target.save(update_fields=["is_active", "approval_status", "approved_by", "approved_at"])
    create_audit_event("admin.reject_user", actor=request.user, target_type="User", target_id=target.id, request=request, result="success", details={"role": target.role})
    messages.success(request, f"Rejected {target.email}.")
    return redirect("accounts:user_management")


@login_required
def doctor_specialization_view(request):
    if not request.user.is_doctor():
        return render(request, "errors/403.html", status=403)
    profile, _ = DoctorProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        specialization_id = request.POST.get("specialization")
        specialization = Specialization.objects.filter(id=specialization_id, is_active=True).first()
        profile.specialization = specialization
        profile.specialization_text = request.POST.get("specialization_text", "").strip()
        profile.qualifications = request.POST.get("qualifications", "").strip()
        profile.years_experience = int(request.POST.get("years_experience") or 0)
        profile.availability = request.POST.get("availability", "").strip()
        profile.save()
        messages.success(request, "Doctor profile updated.")
        return redirect("accounts:doctor_specialization")
    specialties = Specialization.objects.filter(is_active=True).order_by("name")
    return render(request, "accounts/doctor_specialization.html", {"profile": profile, "specialties": specialties})


@login_required
@require_http_methods(["POST"])
def toggle_user_view(request, user_id):
    if not is_admin(request.user):
        return render(request, "errors/403.html", status=403)
    target = get_object_or_404(User, id=user_id)
    if target == request.user:
        messages.error(request, "You cannot deactivate your own account.")
        return redirect("accounts:user_management")
    target.is_active = not target.is_active
    target.save(update_fields=["is_active"])
    create_audit_event("admin.toggle_user", actor=request.user, target_type="User", target_id=target.id, request=request, result="success", details={"is_active": target.is_active})
    messages.success(request, f"User {target.email} updated.")
    return redirect("accounts:user_management")
