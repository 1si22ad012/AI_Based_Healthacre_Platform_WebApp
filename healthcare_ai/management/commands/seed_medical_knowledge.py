from django.core.management.base import BaseCommand

from healthcare_ai.rag import seed_knowledge


class Command(BaseCommand):
    help = "Seed curated public-health knowledge chunks for RAG."

    def handle(self, *args, **options):
        created = seed_knowledge()
        self.stdout.write(self.style.SUCCESS(f"Seeded {created} new knowledge chunks."))