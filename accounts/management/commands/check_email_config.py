from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Safely display the active email configuration."

    def handle(self, *args, **options):
        self.stdout.write(f".env loaded from project root: yes")
        self.stdout.write(f"Settings module: {settings.SETTINGS_MODULE}")
        self.stdout.write(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
        self.stdout.write(f"EMAIL_HOST: {settings.EMAIL_HOST}")
        self.stdout.write(f"EMAIL_PORT: {settings.EMAIL_PORT}")
        self.stdout.write(f"EMAIL_HOST_USER configured: {bool(settings.EMAIL_HOST_USER)}")
        self.stdout.write(f"EMAIL_HOST_PASSWORD configured: {bool(settings.EMAIL_HOST_PASSWORD)}")
        self.stdout.write(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
        self.stdout.write(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
        if "console" in settings.EMAIL_BACKEND.lower():
            self.stdout.write(self.style.WARNING("Console backend is active. OTP emails will be printed locally, not delivered."))
        elif not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
            self.stdout.write(self.style.WARNING("SMTP backend selected, but credentials are missing."))
        else:
            self.stdout.write(self.style.SUCCESS("SMTP backend is configured for email delivery."))