from django.core.management.base import BaseCommand

from accounts.models import Specialization

SPECIALTIES = [
    "General Physician", "Cardiologist", "Pediatrician", "Anesthesiologist",
    "Dentist", "Dermatologist", "Neurologist", "Orthopedic Specialist",
    "Gynecologist", "Ophthalmologist", "Psychiatrist", "ENT Specialist",
    "Oncologist", "Gastroenterologist", "Urologist", "Pulmonologist",
    "Endocrinologist", "Nephrologist",
]


class Command(BaseCommand):
    help = "Seed the initial healthcare specializations."

    def handle(self, *args, **options):
        created = 0
        for name in SPECIALTIES:
            _, was_created = Specialization.objects.get_or_create(name=name)
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f"Seeded specializations. Created {created} new records."))