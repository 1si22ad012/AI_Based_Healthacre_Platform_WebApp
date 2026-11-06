import secrets
from datetime import timedelta

from django.contrib.auth.hashers import make_password
from django.core.cache import cache
from django.utils import timezone

from .models import EmailOTP


OTP_EXPIRY_MINUTES = 5
OTP_RESEND_COOLDOWN_SECONDS = 60
OTP_MAX_ATTEMPTS = 5


def generate_otp() -> str:
    return f"{secrets.randbelow(900000) + 100000:06d}"


def invalidate_previous_otps(user, purpose=EmailOTP.PURPOSE_LOGIN):
    EmailOTP.objects.filter(user=user, purpose=purpose, used_at__isnull=True).update(used_at=timezone.now())


def create_login_otp(user, ip_address=None):
    invalidate_previous_otps(user)
    otp = generate_otp()
    otp_record = EmailOTP.objects.create(
        user=user,
        otp_hash=make_password(otp),
        purpose=EmailOTP.PURPOSE_LOGIN,
        expires_at=timezone.now() + timedelta(minutes=OTP_EXPIRY_MINUTES),
        max_attempts=OTP_MAX_ATTEMPTS,
        ip_address=ip_address,
    )
    return otp, otp_record


def resend_cooldown_remaining(user, purpose=EmailOTP.PURPOSE_LOGIN):
    latest = EmailOTP.objects.filter(user=user, purpose=purpose).order_by("-created_at").first()
    if not latest:
        return 0
    elapsed = (timezone.now() - latest.last_sent_at).total_seconds()
    remaining = OTP_RESEND_COOLDOWN_SECONDS - elapsed
    return max(0, int(remaining))


def verify_login_otp(user, submitted_otp, ip_address=None):
    otp_record = EmailOTP.objects.filter(user=user, purpose=EmailOTP.PURPOSE_LOGIN, used_at__isnull=True).order_by("-created_at").first()
    if not otp_record:
        return False, "No active verification code. Please log in again."

    if otp_record.is_expired:
        otp_record.used_at = timezone.now()
        otp_record.save(update_fields=["used_at"])
        return False, "Your verification code has expired. Please request a new one."

    if otp_record.attempts >= otp_record.max_attempts:
        otp_record.used_at = timezone.now()
        otp_record.save(update_fields=["used_at"])
        return False, "Maximum verification attempts exceeded. Please request a new code."

    otp_record.attempts += 1
    if otp_record.check_otp(submitted_otp.strip()):
        otp_record.used_at = timezone.now()
        otp_record.save(update_fields=["attempts", "used_at"])
        return True, "Verification successful."

    if otp_record.attempts >= otp_record.max_attempts:
        otp_record.used_at = timezone.now()
        otp_record.save(update_fields=["attempts", "used_at"])
        return False, "Maximum verification attempts exceeded. Please request a new code."

    otp_record.save(update_fields=["attempts"])
    return False, "Invalid verification code."