from django.core.management.base import BaseCommand

from security.key_management import reconcile_key_usage


class Command(BaseCommand):
    help = "Reconcile key usage counts with successful EncryptionOperation records."

    def handle(self, *args, **options):
        reconcile_key_usage()
        self.stdout.write(self.style.SUCCESS("Key usage counts reconciled."))