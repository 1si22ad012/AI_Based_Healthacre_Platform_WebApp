import logging
from datetime import datetime

from django.utils import timezone
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from .models import MedicalKnowledgeChunk

logger = logging.getLogger(__name__)

CURATED_KNOWLEDGE = [
    {
        "source_title": "MedlinePlus - Fever",
        "source_url": "https://medlineplus.gov/fever.html",
        "source_type": "public_health",
        "chunk_text": "Fever is a temporary increase in body temperature, often due to an illness. Seek medical care if fever is very high, lasts more than three days, or occurs with severe symptoms.",
        "keywords": ["fever", "temperature", "infection"],
    },
    {
        "source_title": "MedlinePlus - Chest Pain",
        "source_url": "https://medlineplus.gov/chestpain.html",
        "source_type": "public_health",
        "chunk_text": "Chest pain can have many causes, including heart, lung, muscle, and digestive problems. Sudden or severe chest pain, especially with shortness of breath or sweating, requires emergency care.",
        "keywords": ["chest pain", "heart", "emergency", "shortness of breath"],
    },
    {
        "source_title": "WHO - Stroke Warning Signs",
        "source_url": "https://www.who.int/",
        "source_type": "public_health",
        "chunk_text": "Stroke warning signs include sudden numbness, confusion, trouble speaking, vision problems, difficulty walking, and severe headache. Call emergency services immediately.",
        "keywords": ["stroke", "numbness", "confusion", "emergency"],
    },
    {
        "source_title": "MedlinePlus - Headache",
        "source_url": "https://medlineplus.gov/headache.html",
        "source_type": "public_health",
        "chunk_text": "Most headaches are not serious, but sudden severe headache, headache with fever and stiff neck, or headache after injury needs medical attention.",
        "keywords": ["headache", "migraine", "fever", "neck"],
    },
    {
        "source_title": "MedlinePlus - Shortness of Breath",
        "source_url": "https://medlineplus.gov/breathingproblems.html",
        "source_type": "public_health",
        "chunk_text": "Shortness of breath can be caused by heart, lung, or other conditions. Severe or sudden breathing difficulty is an emergency.",
        "keywords": ["breathing", "shortness of breath", "emergency", "lung"],
    },
    {
        "source_title": "MedlinePlus - Diabetes",
        "source_url": "https://medlineplus.gov/diabetes.html",
        "source_type": "public_health",
        "chunk_text": "Diabetes is a chronic condition affecting blood sugar. Management includes diet, exercise, monitoring, and medication prescribed by a clinician.",
        "keywords": ["diabetes", "blood sugar", "medication"],
    },
    {
        "source_title": "MedlinePlus - Hypertension",
        "source_url": "https://medlineplus.gov/highbloodpressure.html",
        "source_type": "public_health",
        "chunk_text": "High blood pressure often has no symptoms but increases risk of heart disease and stroke. Regular monitoring and clinician-guided management are important.",
        "keywords": ["hypertension", "blood pressure", "heart", "stroke"],
    },
    {
        "source_title": "CDC - Emergency Warning Signs",
        "source_url": "https://www.cdc.gov/",
        "source_type": "public_health",
        "chunk_text": "Seek emergency care for difficulty breathing, chest pain, sudden confusion, severe bleeding, or loss of consciousness.",
        "keywords": ["emergency", "breathing", "chest pain", "bleeding", "consciousness"],
    },
]


def seed_knowledge():
    created = 0
    for item in CURATED_KNOWLEDGE:
        obj, was_created = MedicalKnowledgeChunk.objects.get_or_create(
            source_title=item["source_title"],
            chunk_text=item["chunk_text"],
            defaults={
                "source_url": item["source_url"],
                "source_type": item["source_type"],
                "keywords": item["keywords"],
                "version": "v1",
            },
        )
        if was_created:
            created += 1
    return created


def retrieve(query, top_k=None):
    top_k = top_k or getattr(__import__("django.conf", fromlist=["settings"]).settings, "RAG_TOP_K", 4)
    chunks = list(MedicalKnowledgeChunk.objects.all())
    if not chunks or not query.strip():
        return []
    corpus = [c.chunk_text + " " + " ".join(c.keywords or []) for c in chunks]
    try:
        vectorizer = TfidfVectorizer(stop_words="english")
        matrix = vectorizer.fit_transform(corpus + [query])
        q_vec = matrix[-1]
        doc_vecs = matrix[:-1]
        sims = cosine_similarity(q_vec, doc_vecs).flatten()
    except Exception as exc:
        logger.warning("RAG retrieval failed: %s", exc)
        return []
    ranked = sorted(range(len(chunks)), key=lambda i: sims[i], reverse=True)
    results = []
    for idx in ranked[:top_k]:
        if sims[idx] < 0.05:
            continue
        c = chunks[idx]
        results.append({
            "id": c.id,
            "source_title": c.source_title,
            "source_url": c.source_url,
            "chunk_text": c.chunk_text,
            "score": float(sims[idx]),
            "retrieved_at": c.retrieved_at.isoformat() if c.retrieved_at else None,
        })
    return results