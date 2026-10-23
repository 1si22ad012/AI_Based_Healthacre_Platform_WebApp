from django.core.management.base import BaseCommand

from ai_security.training import train_anomaly_models, train_policy_model


class Command(BaseCommand):
    help = "Train and persist AI security models using synthetic, non-patient data."

    def handle(self, *args, **options):
        policy_path = train_policy_model()
        anomaly_paths = train_anomaly_models()
        self.stdout.write(self.style.SUCCESS(f"Policy model saved: {policy_path}"))
        for name, path in anomaly_paths.items():
            self.stdout.write(self.style.SUCCESS(f"{name} saved: {path}"))
