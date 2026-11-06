# Medical RAG Architecture

## Components
- MedicalKnowledgeChunk model (source title, URL, type, text, keywords, version, retrieved_at).
- Curated public-health facts seeded via `python manage.py seed_medical_knowledge`.
- TF-IDF vectorizer + cosine similarity retrieval (scikit-learn).
- Relevance threshold 0.05; top-k (default 4).

## Sources
MedlinePlus, WHO, CDC (curated short paraphrases with attribution). No full copyrighted articles reproduced.