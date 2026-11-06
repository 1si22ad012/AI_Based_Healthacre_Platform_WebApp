from django.core.management.base import BaseCommand

from ai_security.training import train_anomaly_models, train_policy_model


class Command(BaseCommand):
    help = "Train and persist AI security models using synthetic or configured non-patient data."

    def handle(self, *args, **options):
        policy = train_policy_model()
        anomaly = train_anomaly_models()
        self.stdout.write(self.style.SUCCESS(f"Policy model saved: {policy['model']}"))
        self.stdout.write(self.style.SUCCESS(f"Policy metrics: {policy['metrics']}"))
        self.stdout.write(self.style.SUCCESS(f"Anomaly version: {anomaly['version']} dataset: {anomaly['dataset']}"))
        self.stdout.write(self.style.SUCCESS(f"Anomaly metrics: {anomaly['metrics']}"))