# Voice Assistant Implementation Guide

## Architecture
Microphone → Web Speech API → text normalization → intent resolution (healthcare_ai/voice.py) → role validation → allowlisted Django URL → navigation + optional speech synthesis.

## Intent Categories
NAVIGATE, SEARCH, SHOW_INFORMATION, SCROLL, GO_BACK, REFRESH, HELP, STOP_LISTENING, CLOSE_ASSISTANT, UNKNOWN.

## Command Examples
- "open my dashboard", "show my appointments", "find a doctor", "open key management".

## Role Permissions
Patient/Doctor/Lab/Admin allowlists enforced server-side in resolve_voice_command.

## Speech Recognition Flow
Web Speech API (en-IN), error handling, continuous listening, duplicate prevention, text fallback.

## Speech Synthesis Flow
Browser SpeechSynthesis, toggle on/off, no sensitive data spoken.

## Browser Compatibility
Chrome/Edge (Web Speech API). Firefox/Safari limited. Text fallback always available.

## Testing
`python manage.py test healthcare_ai.test_voice_upgrade` and `node --check static/js/voice.js`.