# 🏥 AI-Based Security for Healthcare Applications

An AI-powered healthcare platform that combines secure medical record management, intelligent healthcare assistance, machine-learning-based threat detection, and advanced data protection.

The platform is designed to protect sensitive healthcare information using encryption, role-based access control, email OTP authentication, security monitoring, anomaly detection, and AI-assisted healthcare services.

## 🌐 Live Demo

**Live Application:** [Open Healthcare Security Platform](https://ai-based-healthacre-platform-webapp.onrender.com/)

**GitHub Repository:** [AI-Based Healthcare Platform](https://github.com/1si22ad012/AI_Based_Healthacre_Platform_WebApp)

**Demo Video:** Add your GitHub video attachment or YouTube demonstration link here.

> **Note:** The application is hosted on Render's free plan. The service may spin down after inactivity, so the first request can take additional time to load.

---

## 📌 Project Overview

Healthcare applications manage highly sensitive information, including patient records, prescriptions, laboratory reports, appointments, and medical history.

Unauthorized access, data breaches, suspicious activities, and weak authentication mechanisms can compromise patient privacy.

This project addresses these challenges through a Django-based healthcare platform integrating:

- Secure authentication and role-based authorization.
- AES-GCM encryption and ECC-based cryptographic operations.
- AI-powered healthcare assistance.
- Retrieval-Augmented Generation (RAG).
- Machine-learning-based threat and anomaly detection.
- Historical security risk prediction.
- Security incident management and audit logging.
- Voice-based platform interaction.

The objective is to combine healthcare functionality, data security, and intelligent monitoring in one integrated application.

## 🎯 Project Objectives

- Protect sensitive healthcare information.
- Provide secure user registration and authentication.
- Implement email OTP verification.
- Restrict access according to user roles and permissions.
- Secure medical records using encryption and key management.
- Identify suspicious activities through machine-learning techniques.
- Provide AI-assisted healthcare information and symptom assessment.
- Maintain audit records for security monitoring and accountability.
- Improve healthcare application usability through voice interaction.

---

## ✨ Key Features

### 🔐 1. Authentication and Access Control

- User registration, login, and profile management.
- Six-digit email OTP verification.
- Cryptographically secure OTP generation.
- Hashed OTP storage and expiration handling.
- One-time OTP verification.
- Previous OTP invalidation when a new OTP is generated.
- OTP attempt limits and resend cooldown.
- Session-based authentication after successful verification.
- Role-based access control and dashboard routing.
- Forced password change for designated accounts.

### 👥 2. Role-Based Healthcare Management

The platform supports four major user roles:

- **Patient:** Patient information, appointments, prescriptions, and healthcare assistance.
- **Doctor:** Patient-related workflows and medical information according to assigned permissions.
- **Laboratory Technician:** Laboratory requests and report management.
- **Administrator:** User management, security monitoring, and platform administration.

Role-based navigation and backend authorization are designed to restrict access to protected resources.

### 🔒 3. Advanced Healthcare Data Security

- AES-GCM authenticated encryption.
- ECC-based cryptographic operations.
- HKDF-based key derivation.
- Environment-based master secret configuration.
- Key metadata and lifecycle management.
- Key activation and expiration tracking.
- Key usage tracking.
- Key rotation and version-aware key management.
- Role-based decryption permissions.
- Security event recording.

The system is designed to protect medical information while maintaining controlled access to encrypted records.

### 🤖 4. AI Healthcare Chatbot

An AI-assisted healthcare chatbot that provides healthcare-related information through an integrated LLM and retrieval-based architecture.

Features include:

- OpenAI-compatible LLM provider integration.
- Configurable LLM model and API endpoint.
- Medical knowledge retrieval.
- Context-aware responses using retrieved information.
- Conversation history management.
- User-specific conversation ownership and isolation.
- Source attribution for retrieved medical knowledge.
- Emergency-related response detection.
- Safety filtering and fallback responses.

**Technology:** Python, Django, LLM integration, TF-IDF retrieval, and RAG.

**Configuration:** The external LLM requires a valid provider API key. Without it, the application can use its configured fallback and retrieval functionality.

### 📚 5. Retrieval-Augmented Generation (RAG)

The medical RAG component improves chatbot responses by retrieving relevant information from a medical knowledge collection.

Implemented capabilities:

- Medical knowledge storage.
- Medical knowledge chunking.
- TF-IDF-based document retrieval.
- Relevant context selection.
- Context-assisted LLM responses.
- Retrieved-source attribution.
- Configurable retrieval count using `RAG_TOP_K`.

This approach combines retrieved medical information with language-model-generated responses.

### 🩺 6. AI-Assisted Symptom Assessment

A structured symptom assessment module that collects relevant information to support healthcare guidance.

Implemented fields and capabilities include:

- Symptom description.
- Duration of symptoms.
- Severity.
- Medical history.
- Medication information.
- Allergy information.
- Structured assessment responses.
- Safety-oriented guidance.
- Healthcare specialty recommendations.

Specialty recommendations currently use rule-based and keyword-based logic.

**Important:** Symptom assessment provides decision support and is not a medical diagnosis or replacement for professional medical consultation.

### 🧠 7. Machine-Learning-Based Threat Detection

The platform integrates multiple machine-learning algorithms for security analysis.

Implemented algorithms:

**Random Forest**
- Supervised security classification.
- Normal and attack-pattern classification.

**Isolation Forest**
- Unsupervised anomaly detection.
- Identification of unusual activity patterns.

**One-Class SVM**
- Anomaly detection using learned normal activity patterns.
- RBF kernel configuration.

Implemented security features include:

- Model training and model artifact management.
- Security feature extraction.
- Anomaly scoring.
- Suspicious activity identification.
- Model registry information.
- Security model evaluation reporting.

The system uses security-related features such as failed logins, login frequency, unusual access hours, denied requests, record access counts, encryption failures, upload sizes, and suspicious request parameters.

**Important:** The current model training has used synthetic security data unless a real dataset is configured. Real-world validation is required before production security decisions are based on model predictions.

### 📊 8. Historical Security Risk Prediction

A historical risk analysis component that evaluates security activity over time.

Features include:

- Historical security activity aggregation.
- Risk score calculation.
- Risk categories.
- Security trend analysis.
- User-related risk information.
- Dashboard-oriented risk summaries.

The risk score is an application-level security indicator and should not be interpreted as a clinically validated or universally calibrated probability.

### 🚨 9. AI Anomaly Monitoring and Security Incident Management

The security monitoring system provides visibility into suspicious application activity.

Features include:

- Persistent anomaly detection records.
- Anomaly feature information.
- Detection reasons and associated security events.
- Anomaly history.
- Detailed anomaly views.
- Security incident creation.
- Incident acknowledgement.
- Investigation workflow.
- Incident resolution.
- False-positive classification.
- Security notifications and audit records.

### 🔑 10. Security Key Management Dashboard

- Key metadata management.
- Key activation and expiration information.
- Key usage counters.
- Key rotation history.
- Key activity tracking.
- Key lifecycle monitoring.
- Key usage reconciliation command.

### 🎙️ 11. Voice Assistant

The healthcare platform includes a browser-based voice assistant.

Features include:

- Browser speech recognition.
- Live speech transcription.
- Editable text commands.
- Voice command processing.
- Shared text and voice command execution.
- Role-aware platform navigation.
- Speech input through supported browser microphone interfaces.

The implementation uses the browser Web Speech API and application-side command resolution.

### 📷 12. Face Verification Prototype

- Prototype face-verification functionality.
- Additional identity-verification workflow.
- Optional integration with the healthcare interface.

This is an experimental prototype and does not provide production-grade biometric identity assurance or guaranteed liveness detection.

### 📋 13. Audit Logging and Notifications

- Application activity logging.
- Security event tracking.
- Audit records.
- Security-related notifications.
- Incident-related audit information.
- Monitoring and accountability support.

### 📈 14. Administrator Security Dashboard

- Security monitoring overview.
- Anomaly statistics.
- Security risk information.
- High-risk account information.
- Dashboard analytics and charts.
- Security incident monitoring.
- Key management access.

---

## 🏗️ Project Architecture and Django Modules

The application follows a modular Django architecture.

| Module | Responsibility |
|---|---|
| `accounts` | Registration, login, email OTP, profiles, and role management |
| `patients` | Patient information management |
| `appointments` | Appointment management |
| `prescriptions` | Prescription operations |
| `laboratory` | Laboratory requests and reports |
| `security` | Encryption, key management, and access security |
| `ai_security` | ML threat detection and anomaly analysis |
| `audit` | Application activity and security audit records |
| `notifications` | Notification functionality |
| `healthcare_ai` | Chatbot, RAG, symptom assessment, risk analysis, and voice commands |
| `config` | Django settings, routing, and ASGI configuration |

### Main Project Structure

```text
AI_Based_Healthacre_Platform_WebApp/
│
├── accounts/
├── patients/
├── appointments/
├── prescriptions/
├── laboratory/
├── security/
├── ai_security/
├── audit/
├── notifications/
├── healthcare_ai/
│
├── config/
├── templates/
├── static/
├── ml_artifacts/
│
├── manage.py
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🛠️ Technologies Used

| Category | Technologies |
|---|---|
| Programming Language | Python |
| Backend Framework | Django |
| REST API | Django REST Framework |
| Frontend | HTML, CSS, JavaScript |
| Database | SQLite for local development; production database depends on deployment configuration |
| ASGI Server | Daphne |
| Real-time Communication | Django Channels |
| Machine Learning | Scikit-learn |
| ML Algorithms | Random Forest, Isolation Forest, One-Class SVM |
| AI Integration | OpenAI-compatible LLM integration |
| RAG | TF-IDF-based retrieval |
| Encryption | AES-GCM, ECC, HKDF |
| Speech Recognition | Browser Web Speech API |
| API Documentation | drf-spectacular / Swagger UI, where configured |
| Deployment | Render |
| Version Control | Git and GitHub |

---

## ⚙️ Run the Project Locally

### Prerequisites

- Python 3.13 or another version supported by the project dependencies.
- Git.
- Visual Studio Code (recommended).

### Step 1: Clone the repository

```bash
git clone https://github.com/1si22ad012/AI_Based_Healthacre_Platform_WebApp.git

cd AI_Based_Healthacre_Platform_WebApp
```

### Step 2: Create a virtual environment

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

Then activate the environment again.

### Step 3: Install dependencies

```powershell
python -m pip install --upgrade pip

pip install -r requirements.txt
```

### Step 4: Configure environment variables

Create a local `.env` file using `.env.example` as a reference.

Configure the required values, including:

- Django secret key.
- Debug and allowed-host settings.
- Database configuration.
- Email SMTP configuration.
- Encryption master secret.
- Optional LLM provider configuration.

Example optional LLM configuration:

```env
LLM_PROVIDER=
LLM_API_KEY=
LLM_MODEL=gpt-4o-mini
LLM_BASE_URL=https://api.openai.com/v1
LLM_TIMEOUT=30
RAG_TOP_K=4
```

**Security:** Never commit your actual `.env` file, API keys, SMTP passwords, encryption secrets, or database credentials to GitHub.

### Step 5: Apply database migrations

```powershell
python manage.py migrate
```

### Step 6: Create an administrator account

```powershell
python manage.py createsuperuser
```

Follow the prompts to configure the account.

### Step 7: Start the development server

```powershell
python manage.py runserver
```

Open the application:

- Website: http://127.0.0.1:8000/
- Admin panel: http://127.0.0.1:8000/admin/
- Health check: http://127.0.0.1:8000/healthz/
- API documentation: http://127.0.0.1:8000/api/docs/ (if configured and accessible)

### Optional: Seed Medical Knowledge

If the medical knowledge seeding command is available in your environment:

```powershell
python manage.py seed_medical_knowledge
```

### Optional: Train Security Models

The project includes a security model training command:

```powershell
python manage.py train_security_models
```

Training data and model output configuration must be checked before running this command.

### Optional: Reconcile Key Usage

```powershell
python manage.py reconcile_key_usage
```

### Run Tests

```powershell
python manage.py test
```

A previous test run completed with **108 tests passing**. Re-run the test suite after subsequent changes to confirm the current code state.

---

## 🚀 Deployment

The application is deployed on **Render** and connected to the GitHub `main` branch.

**Live Application:**

https://ai-based-healthacre-platform-webapp.onrender.com/

**Deployment Configuration:**

- Platform: Render Web Service.
- Server: Daphne.
- Application entry point: `config.asgi:application`.
- Deployment branch: `main`.
- Automatic deployment: Enabled for the connected repository.

Production deployment also requires correct environment variables, database configuration, database migrations, email configuration, and static-file configuration.

A successful deployment should be verified through Render Events and Logs.

---

## 🔒 Security and Privacy Considerations

- Use synthetic patient information for development and demonstrations.
- Never upload real patient records or personally identifiable medical information to public repositories.
- Store passwords, API keys, and encryption secrets in environment variables.
- Enforce authorization checks before accessing protected healthcare records.
- Use HTTPS for deployed applications.
- Review encryption key management and database permissions.
- Validate security model predictions before operational use.
- Maintain appropriate database backups and monitoring.
- Follow applicable healthcare privacy and regulatory requirements before real-world deployment.

---

## ⚠️ Current Limitations

- External LLM responses require valid provider credentials; fallback functionality is available when the external provider is not configured.
- ML threat-detection training has used synthetic data unless a real dataset is supplied.
- Symptom-to-specialty recommendations are currently rule-based.
- Symptom assessment is not a medical diagnosis.
- Face verification is a prototype, not production-grade biometric authentication.
- Voice recognition depends on browser support and microphone permissions.
- Production role workflows and access permissions should be verified with separate accounts for each role.
- Production database migrations, backups, and environment configuration must be monitored.

---

## 🛣️ Future Enhancements

- Train and evaluate threat-detection models using appropriately governed real-world datasets.
- Improve real-time anomaly detection and security alerting.
- Expand medical knowledge coverage and evaluate AI response quality.
- Improve healthcare chatbot context handling.
- Enhance role-specific healthcare workflows.
- Strengthen biometric identity verification and liveness checks.
- Expand security analytics and reporting.
- Improve deployment automation, monitoring, and backup procedures.
- Perform comprehensive end-to-end and security testing.

---

## 👩‍💻 Author

**Deepthi U**

Bachelor of Engineering – Artificial Intelligence and Data Science

GitHub: [1si22ad012](https://github.com/1si22ad012)

---

## 📄 License

No open-source license is currently specified. Add a LICENSE file if you intend to distribute this project under an open-source license.

---

**Project Purpose:** Educational and application-development project demonstrating the integration of healthcare workflows, AI assistance, machine learning, cryptographic security, and application monitoring.

*This platform is not a substitute for professional medical advice, diagnosis, or treatment.*
