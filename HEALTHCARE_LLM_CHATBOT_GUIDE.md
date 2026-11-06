# Healthcare LLM Chatbot Guide

## Configuration
Set in .env:
LLM_PROVIDER, LLM_API_KEY, LLM_MODEL, LLM_BASE_URL, LLM_TIMEOUT, RAG_TOP_K

If LLM_API_KEY is blank, the chatbot uses a safe rule-based fallback and RAG retrieval.

## Architecture
User message → conversation lookup → emergency detection → RAG retrieval (TF-IDF) → LLM call (if configured) → safety filter → source attribution → storage.

## Safety
System prompt prohibits diagnosis/prescription. Post-response filter blocks unsafe phrases. Emergency keywords trigger immediate advice.

## Privacy
Only the user message and retrieved public-health chunks are sent to the provider. No patient records or identifiers.