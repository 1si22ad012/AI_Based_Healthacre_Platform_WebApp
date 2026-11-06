# AI-Based Security for Healthcare Applications — Feature Audit Report

## 1. Project Architecture

### Technology Stack
- Backend: Python, Django 5.2.17, Django REST Framework
- ASGI server: Daphne
- Real-time: Django Channels, WebSocket consumer at `/ws/security/`
- Database: SQLite for local development, PostgreSQL supported through `DATABASE_URL`
- Channel layer: Redis when `REDIS_URL` is set, otherwise in-memory
- Static files: WhiteNoise
- ML: scikit-learn, NumPy, Pandas, joblib
- Cryptography: `cryptography` (AES-GCM, ECC, RSA helpers)

### Django Applications
- `accounts`: users, roles, profiles, registration, OTP login, specialization
- `patients`: encrypted medical records and diagnoses
- `appointments`: appointment scheduling
- `prescriptions`: encrypted prescriptions and ECDSA signatures
- `laboratory`: lab requests and encrypted reports
- `security`: AES-GCM, key management, policy demo
- `ai_security`: adaptive encryption policy and anomaly detection
- `audit`: security events, anomaly alerts, audit log, WebSocket consumer
- `notifications`: user notifications and real-time delivery
- `healthcare_ai`: symptom assessment, chatbot, doctor search, risk scoring, incidents, voice/face prototypes

### Communication Flow
```text
Browser templates/forms
  -> Django views / DRF APIs
    -> service classes
      -> models / database
      -> ML artifacts (ml_artifacts/*.joblib)
      -> audit and notification services
      -> WebSocket channel layer
```

All protected healthcare data is encrypted before persistence. Decryption occurs only after server-side authorization.

---

## 2. Complete AI Feature Inventory

| Feature | Type | Backend | Frontend | Database | Automated Tests | Overall Status |
|---|---|---|---|---|---|---|
| Adaptive encryption policy | Random Forest ML | Implemented | Policy demo page | EncryptionOperation | Yes | Implemented, partially verified |
| Anomaly detection | Isolation Forest, One-Class SVM, Random Forest | Implemented | Monitoring and alert pages | SecurityEvent, AnomalyAlert | Yes | Implemented, partially verified |
| Security risk scoring | Deterministic weighted scoring | Implemented | Risk analysis page | SecurityEvent metadata | Yes | Implemented, partially verified |
| Explainable security analysis | Rule-based reasons | Implemented | Risk analysis page | Audit details | Yes | Implemented, partially verified |
| Security incident management | Deterministic workflow | Implemented | Incident pages | SecurityIncident | Yes | Implemented, partially verified |
| Incident summarization | Deterministic NLP/rule-based | Implemented | Incident summary page | SecurityIncident | Yes | Implemented, partially verified |
| Healthcare chatbot | Rule-based keyword assistant | Implemented | Chatbot page | AIConversation | Yes | Implemented, partially verified |
| Symptom assessment | Rule-based keyword classifier | Implemented | Assessment page | SymptomAssessment | Yes | Implemented, partially verified |
| Doctor recommendation | Database filtering by specialty | Implemented | Assessment results | DoctorProfile, Specialization | Yes | Implemented, partially verified |
| Doctor specialization management | Relational model | Implemented | Doctor profile page | Specialization, DoctorProfile | Limited | Implemented, partially verified |
| Voice assistant | Browser Speech API + JS | Resolver tested | Voice panel | None | Yes (resolver) | Partially implemented |
| Face verification | Prototype, consent + hash | Implemented prototype | Enrollment page | FaceVerificationRecord | Limited | UI / demo |
| Email OTP login | Secure OTP service | Implemented | OTP page | EmailOTP | Yes | Implemented, partially verified |
| Login email notification | SMTP email | Implemented | None | LoginAudit | Yes | Implemented, partially verified |
| Application notifications | Database + WebSocket | Implemented | Notification pages | Notification | Limited | Implemented, partially verified |

---

## 3. Feature-by-Feature Findings

### A. AI Cybersecurity Threat Detection

Implemented files:
- `ai_security/services.py`
- `ai_security/training.py`
- `ai_security/views.py`
- `audit/models.py`
- `audit/services.py`

Actual ML models:
- Random Forest classifier for adaptive encryption policy
- Isolation Forest for unsupervised anomaly detection
- One-Class SVM for suspicious behavior detection
- Supervised Random Forest for anomaly classification

Dataset:
- Synthetic, generated in `ai_security/training.py`
- No real patient data is used
- Feature values include failed logins, login frequency, upload size, CPU, record access, encryption failures, invalid tags, and suspicious parameters

Model persistence:
- `ml_artifacts/policy_random_forest.joblib`
- `ml_artifacts/isolation_forest.joblib`
- `ml_artifacts/one_class_svm.joblib`
- `ml_artifacts/anomaly_random_forest.joblib`

Integration:
- `patients/services.py` calls `detect_anomaly()` during record creation
- `patients/services.py` calls `select_policy()` before encryption
- `ai_security/views.py` runs detection from the admin demo page
- Security events and alerts are stored in `SecurityEvent` and `AnomalyAlert`

False-positive handling:
- Combined detector score threshold is `0.5`
- Mandatory security rules can override model recommendations
- Safe fallback is used when models are unavailable
- Rule-based fallback is used when model artifacts are missing

Evidence:
- `ai_security/tests.py` verifies policy selection, fallback, invalid features, and anomaly results
- `patients/tests.py` verifies anomalous requests are blocked

### B. Intelligent Security Risk Scoring

Implemented files:
- `healthcare_ai/services.py`
- `healthcare_ai/views.py`
- `healthcare_ai/templates/.../risk_analysis.html`

Implementation:
- `calculate_risk_score()` returns a score from 0 to 100
- Weighted factors:
  - Failed logins
  - Denied requests
  - Invalid authentication tags
  - Unusual hour
  - Anomaly detection result
- Classification:
  - Low: 0-29
  - Medium: 30-59
  - High: 60-79
  - Critical: 80-100
- `explain_risk()` returns human-readable reasons

Integration:
- Login risk is calculated in `accounts/views.py`
- Risk reasons are stored in audit event details
- Admin-only risk analysis page is available

Evidence:
- `healthcare_ai/tests.py` verifies score calculation and classification

### C. Healthcare AI Chatbot

Implemented files:
- `healthcare_ai/services.py`
- `healthcare_ai/views.py`
- `healthcare_ai/models.py`
- `templates/healthcare_ai/chatbot.html`

Implementation type:
- Rule-based keyword response system
- Not an LLM
- No external API dependency

Safety:
- Does not diagnose
- Does not prescribe
- Directs users to consult qualified healthcare professionals
- Conversation history is user-specific

Evidence:
- `AIConversation` model stores user messages and responses
- `healthcare_ai/tests.py` verifies chatbot response and conversation creation

### D. Symptom Assessment and Doctor Recommendation

Implemented files:
- `healthcare_ai/services.py`
- `healthcare_ai/views.py`
- `healthcare_ai/models.py`
- `accounts/models.py` (`Specialization`, `DoctorProfile`)
- `templates/healthcare_ai/symptom_assessment.html`

Implementation type:
- Rule-based keyword classifier
- Not a trained ML model

Features:
- Single and multiple symptom matching
- Specialty ranking by keyword match count
- Emergency keyword detection
- Safe fallback to General Physician
- Doctor recommendations by specialization
- Assessment history stored in `SymptomAssessment`

Safety:
- Explicitly states that it is preliminary navigation, not diagnosis
- Emergency symptoms direct users to immediate medical care

Evidence:
- `healthcare_ai/tests.py` verifies classification, emergency handling, fallback, and doctor recommendation

### E. AI Security Incident Management

Implemented files:
- `healthcare_ai/models.py`
- `healthcare_ai/views.py`
- `healthcare_ai/services.py`
- `audit/services.py`
- `templates/healthcare_ai/security_incidents.html`
- `templates/healthcare_ai/incident_summary.html`

Implementation:
- `SecurityIncident` model with status workflow
- Statuses: New, Under Investigation, Acknowledged, Resolved, False Positive
- Incidents are created from high-risk security events
- Incidents link to actual `SecurityEvent` records
- Event details include timestamp, event type, actor, severity, and risk score
- Admin-only views for management and summary

Evidence:
- `healthcare_ai/tests.py` verifies incident-event linking
- `audit/tests.py` verifies security event and WebSocket delivery

### F. Voice Assistant

Implemented files:
- `static/js/voice.js`
- `static/css/app.css`
- `healthcare_ai/voice.py`
- `healthcare_ai/views.py`
- `healthcare_ai/urls.py`

Implementation type:
- Browser Web Speech API
- Deterministic Python command resolver
- Role-aware URL resolution

Features:
- Natural-language command normalization
- Synonyms and alternative phrases
- Role-based navigation
- Text command fallback
- Listening/processing/success/error states
- Unsupported browser handling
- Microphone permission handling
- Help and stop commands

Evidence:
- `healthcare_ai/tests.py` verifies normalization, variations, punctuation, case, roles, actions, and empty input
- `node --check static/js/voice.js` passes

Limitation:
- Speech recognition depends on browser support and is not a server-side speech service.

### G. Face Verification Prototype

Implemented files:
- `healthcare_ai/models.py`
- `healthcare_ai/views.py`
- `templates/healthcare_ai/face_verification.html`

Implementation type:
- Prototype only

Features:
- Explicit consent
- Enrollment status
- Template hash storage
- Enrollment removal
- Password login remains available

Limitation:
- No robust liveness detection
- No real biometric matching
- Stores only a hash, not a reliable biometric template
- Should be documented as a prototype

### H. Email OTP and Login Security

Implemented files:
- `accounts/models.py`
- `accounts/otp.py`
- `accounts/views.py`
- `templates/accounts/verify_otp.html`

Features:
- Cryptographically secure six-digit OTP
- Hashed OTP storage
- 5-minute expiry
- Single-use enforcement
- 5 attempt limit
- 60-second resend cooldown
- Rate limiting
- Session-based pending authentication
- SMTP email delivery
- Login audit and risk scoring

Evidence:
- `accounts/tests.py` includes 23 passing tests covering OTP generation, verification, expiry, reuse, resend, cooldown, attempts, role access, and email failure

### I. Notifications and Automated Security Alerts

Implemented files:
- `notifications/models.py`
- `notifications/views.py`
- `audit/services.py`
- `accounts/views.py`
- `appointments/services.py`
- `prescriptions/services.py`
- `laboratory/services.py`

Features:
- User-specific notifications
- Read/unread status
- Notification history
- Real-time WebSocket delivery
- Notifications for appointments, prescriptions, lab reports, professional approval, and high-risk security events

Evidence:
- `audit/tests.py` verifies WebSocket delivery
- `accounts/tests.py` verifies login notification behavior

---

## 4. End-to-End Feature Tracing

### Record Creation Flow
```text
Doctor form
  -> patients/views.py:create_record_view
    -> patients/services.py:encrypt_medical_record
      -> ai_security/services.py:detect_anomaly
      -> ai_security/services.py:select_policy
      -> security/services.py:aes_encrypt
      -> patients/models.py:MedicalRecord
      -> audit/services.py:create_audit_event
```

### Login Flow
```text
Login form
  -> accounts/views.py:login_view
    -> authenticate()
    -> accounts/otp.py:create_login_otp
    -> send_mail()
    -> session stores pending OTP user
  -> accounts/views.py:verify_otp_view
    -> accounts/otp.py:verify_login_otp
    -> login()
    -> role-based dashboard
```

### Incident Flow
```text
Security event
  -> audit/services.py:create_security_event
    -> healthcare_ai/services.py:create_incident_for_security_event
      -> healthcare_ai/models.py:SecurityIncident
  -> admin views manage status
```

### Voice Flow
```text
Browser speech
  -> static/js/voice.js
    -> POST /healthcare/voice-command/
      -> healthcare_ai/views.py:voice_command_view
        -> healthcare_ai/voice.py:resolve_voice_command
      -> JSON response
    -> browser navigation
```

---

## 5. Machine Learning Quality Audit

### Policy Random Forest
- Algorithm: Random Forest Classifier
- Dataset: Synthetic, generated in `ai_security/training.py`
- Features: sensitivity, role, file size, CPU, latency, recent security events, anomaly score, access frequency, risk level
- Evaluation method: synthetic train/test split
- Metrics from independent audit run:
  - Accuracy: 0.9967
  - Macro precision: 0.9883
  - Macro recall: 0.9952
  - Macro F1: 0.9916

### Anomaly Random Forest
- Algorithm: Random Forest Classifier
- Dataset: Synthetic normal and attack samples
- Metrics from independent audit run:
  - Accuracy: 1.0000
  - Precision: 1.0000
  - Recall: 1.0000
  - F1: 1.0000

### Isolation Forest
- Algorithm: Isolation Forest
- Evaluation on held-out synthetic normal and attack data:
  - Precision: 0.9184
  - Recall: 1.0000
  - F1: 0.9574

### One-Class SVM
- Algorithm: One-Class SVM
- Evaluation on held-out synthetic normal and attack data:
  - Precision: 0.9045
  - Recall: 1.0000
  - F1: 0.9499

### ML Limitations
- All datasets are synthetic.
- Metrics are not clinical or real-world security benchmarks.
- The anomaly models may produce false positives on unusual but legitimate development activity.
- Risk scoring is deterministic and not a calibrated probability.
- No SHAP or formal feature-importance visualization is implemented.
- The chatbot and symptom assessment are rule-based, not trained ML models.

---

## 6. Security and Healthcare Safety Audit

### Verified
- Role-based dashboard access
- Patient profile isolation
- Unauthorized record decryption rejected
- Admin-only security pages
- CSRF protection on forms
- DRF authentication and permissions
- File upload validation
- AES-GCM authenticated encryption
- Ciphertext tampering detection
- Hash-chained audit logging
- OTP verification before dashboard access
- Sensitive data excluded from audit logs
- Chatbot safety restrictions
- Emergency symptom warnings

### Issues and Risks
1. **Face verification is a prototype**
   - File: `healthcare_ai/views.py`
   - Impact: Should not be represented as reliable biometric authentication

2. **Voice assistant depends on browser APIs**
   - File: `static/js/voice.js`
   - Impact: Not available in all browsers

3. **Synthetic ML datasets**
   - Files: `ai_security/training.py`
   - Impact: Metrics are not real-world security performance

4. **Admin notification noise**
   - File: `audit/services.py`
   - Impact: High/critical events create notifications for all admins, including policy blocks

5. **Patient list exposure to administrators**
   - File: `patients/views.py`
   - Impact: Administrators can view patient metadata but cannot decrypt records; this is acceptable but should be documented

6. **Audit hash chain is not tamper-proof**
   - File: `audit/services.py`
   - Impact: An attacker with database write access could rewrite the chain

---

## 7. Automated Test Results

Commands executed:
```text
python manage.py check
python manage.py makemigrations --check --dry-run
node --check static/js/voice.js
node --check static/js/app.js
python manage.py test accounts
python manage.py test patients
python manage.py test healthcare_ai
python manage.py test audit ai_security
python manage.py test security laboratory appointments prescriptions notifications
```

Results:
- Django system check: **0 issues**
- Migration check: **No changes detected**
- JavaScript syntax: **valid**
- Accounts: **23 tests passed**
- Patients: **16 tests passed**
- Healthcare AI: **19 tests passed**
- Audit and AI security: **9 tests passed**
- Security, laboratory, appointments, prescriptions, notifications: **10 tests passed**

A full single `python manage.py test` run exceeded the local command timeout, so verification was performed by targeted suites.

---

## 8. Manual Testing Checklist

### Patient
- Register a patient account
- Log in and complete OTP
- View dashboard
- View own records
- Book appointment
- View prescriptions and lab reports
- Use symptom assessment
- Use chatbot
- Use voice assistant text fallback

### Doctor
- Log in with approved doctor account
- View dashboard
- Create encrypted record
- Issue prescription
- Request lab test
- Update specialization
- Search doctors

### Laboratory Technician
- Log in with approved lab account
- View assigned requests
- Upload encrypted report
- View reports

### Administrator
- Log in with admin account
- View admin dashboard
- Manage users
- Review pending professionals
- Review security events
- Manage incidents
- Run risk analysis
- Review audit log

---

## 9. Final Feature Scorecard

| Feature | Implementation Type | Backend | Frontend | Database | Automated Tests | Functional Verification | Security Status | Overall Status | Missing Work |
|---|---|---|---|---|---|---|---|---|---|
| Adaptive encryption | ML | Yes | Yes | Yes | Yes | Yes | Strong | IMPLEMENTED, PARTIALLY VERIFIED | Real-world validation |
| Anomaly detection | ML | Yes | Yes | Yes | Yes | Yes | Strong | IMPLEMENTED, PARTIALLY VERIFIED | Threshold tuning |
| Risk scoring | Deterministic | Yes | Yes | Yes | Yes | Yes | Strong | IMPLEMENTED, PARTIALLY VERIFIED | Calibration |
| Explainable AI | Rule-based | Yes | Yes | Yes | Yes | Yes | Strong | IMPLEMENTED, PARTIALLY VERIFIED | SHAP/feature importance |
| Incident management | Deterministic | Yes | Yes | Yes | Yes | Yes | Strong | IMPLEMENTED, PARTIALLY VERIFIED | Richer history |
| Incident summarization | Deterministic NLP | Yes | Yes | Yes | Yes | Yes | Strong | IMPLEMENTED, PARTIALLY VERIFIED | Better event linking |
| Chatbot | Rule-based | Yes | Yes | Yes | Yes | Yes | Strong | IMPLEMENTED, PARTIALLY VERIFIED | LLM optional |
| Symptom assessment | Rule-based | Yes | Yes | Yes | Yes | Yes | Strong | IMPLEMENTED, PARTIALLY VERIFIED | Clinical validation |
| Doctor recommendation | Database filtering | Yes | Yes | Yes | Yes | Yes | Strong | IMPLEMENTED, PARTIALLY VERIFIED | Availability logic |
| Doctor specialization | Relational | Yes | Yes | Yes | Limited | Yes | Strong | IMPLEMENTED, PARTIALLY VERIFIED | More tests |
| Voice assistant | Browser API + JS | Partial | Yes | No | Resolver only | Partial | Moderate | PARTIALLY IMPLEMENTED | Browser limitations |
| Face verification | Prototype | Prototype | Yes | Yes | Limited | Prototype only | Moderate | UI ONLY / DEMO | Liveness and matching |
| Email OTP login | Secure OTP | Yes | Yes | Yes | Yes | Backend verified | Strong | IMPLEMENTED, PARTIALLY VERIFIED | Real SMTP verification |
| Login notifications | Email automation | Yes | No dedicated UI | Yes | Yes | Backend verified | Strong | IMPLEMENTED, PARTIALLY VERIFIED | User preference controls |
| Notifications | Database + WebSocket | Yes | Yes | Yes | Limited | Backend verified | Strong | IMPLEMENTED, PARTIALLY VERIFIED | Broader coverage |

---

## 10. Prioritized Improvement Plan

### Critical
- None identified in the current code after the recent fixes.

### High
1. Face verification must not be described as production biometric authentication.
   - Files: `healthcare_ai/views.py`, `healthcare_ai/models.py`
   - Fix: Document prototype limitations and avoid relying on it for access.

2. Voice assistant is browser-dependent.
   - File: `static/js/voice.js`
   - Fix: Keep text fallback and document browser support.

### Medium
1. Add more notification coverage.
   - Files: workflow services
   - Fix: Add notifications for all important clinical and security events.

2. Add richer incident history.
   - Files: `healthcare_ai/models.py`, `healthcare_ai/views.py`
   - Fix: Add incident notes and investigation timeline.

3. Add ML model evaluation artifacts.
   - Files: `ai_security/training.py`
   - Fix: Save evaluation metrics and confusion matrices.

### Low
1. Improve UI polish.
2. Add API serializers for AI endpoints.
3. Add performance caching.
4. Improve documentation.

---

## 11. Simple Explanation for Interview

This project is a secure healthcare platform. Patient records are encrypted with AES-GCM before storage. The system uses machine learning to recommend an encryption policy and detect suspicious behavior. It includes role-based dashboards, appointment and prescription workflows, laboratory reporting, audit logging, OTP login, notifications, and real-time alerts.

The AI features are practical but mostly deterministic or trained on synthetic data. The chatbot and symptom checker use safe rule-based logic rather than claiming medical diagnosis. Security controls are implemented server-side, and tests verify the main workflows.

The strongest parts are encryption, role-based access, audit logging, OTP authentication, and the AI security pipeline. The prototype parts are voice assistance and face verification. No production database was modified during this audit.
