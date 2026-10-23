# 🏥 AI-Based Security for Healthcare Applications

An AI-powered healthcare security platform designed to protect sensitive medical information through encryption, role-based access control, AI-based anomaly detection, and security auditing.

## 🌐 Live Demo

**Live Application:** [Open Healthcare Security Platform](https://ai-based-healthacre-platform-webapp.onrender.com/)

**Demo Video:** *Add your GitHub video attachment or YouTube demo link here.*

> **Note:** The application is hosted on Render's free plan, so the first request after inactivity may take some time to load.

## 📌 Project Overview

Healthcare applications manage sensitive information such as patient records, prescriptions, laboratory reports, and appointments. Unauthorized access, data breaches, and suspicious activities can compromise patient privacy.

This project aims to improve healthcare data security by combining encryption techniques, authentication, access control, AI-based security analysis, and audit logging in a web-based application.

## 🎯 Objectives

- Protect sensitive healthcare information.
- Provide secure user registration and authentication.
- Restrict access according to user roles and permissions.
- Support secure management of healthcare records.
- Identify potentially suspicious activities using AI/ML techniques.
- Maintain audit logs for security monitoring and accountability.

## ✨ Key Features

### 🔐 1. Authentication and Access Control
- User registration and login.
- Role-based dashboard routing.
- Patient dashboard access is currently available in the deployed application.
- Access for other roles requires further implementation or troubleshooting.

### 🩺 2. Patient Dashboard
- Patient-oriented dashboard interface.
- Access to patient-related healthcare features supported by the current implementation.

### 🔒 3. Healthcare Security
- AES-GCM encryption functionality.
- ECC-based cryptographic operations.
- Security-related modules for protecting healthcare information.

### 🤖 4. AI-Based Security
- Machine-learning-based security analysis.
- Random Forest, Isolation Forest, and SVM techniques where implemented.

### 📋 5. Audit and Notifications
- Audit logging functionality.
- Notification-related modules.

## 🏗️ Project Modules

The project contains the following Django applications:

- **Accounts:** User registration, login, profiles, and role-based routing.
- **Patients:** Patient information management.
- **Appointments:** Appointment management.
- **Prescriptions:** Prescription-related operations.
- **Laboratory:** Laboratory information management.
- **Security:** Security-related operations.
- **AI Security:** AI/ML-based security analysis.
- **Audit:** Application activity logging.
- **Notifications:** Notification-related functionality.

The presence of a module does not necessarily mean that every feature is currently accessible through the deployed user interface.

## ⚠️ Current Limitations

- The deployed application currently provides dashboard access for the Patient role.
- Dashboard access for other roles, such as doctors, laboratory technicians, and administrators, needs to be verified and completed where necessary.
- Role-specific permissions and navigation require testing for each account type.
- Further testing is needed before considering the application production-ready.

## 🛣️ Future Enhancements

- Enable and verify dashboards for all intended user roles.
- Implement and test role-specific access permissions.
- Complete doctor, laboratory technician, and administrator workflows.
- Improve security monitoring and anomaly detection.
- Strengthen authorization checks for sensitive healthcare records.
- Perform end-to-end testing of registration, login, dashboards, and protected routes.


## 🛠️ Technologies Used

| Category | Technologies |
|---|---|
| Backend | Python, Django |
| API | Django REST Framework |
| Database | SQLite for local development; production database depends on deployment configuration |
| ASGI Server | Daphne |
| Security | AES-GCM, ECC |
| Machine Learning | Random Forest, Isolation Forest, SVM |
| API Documentation | drf-spectacular, Swagger UI |
| Deployment | Render |
| Version Control | Git and GitHub |

## 🏗️ Project Modules

- **Accounts:** Registration, login, profiles, and user management.
- **Patients:** Patient-related information management.
- **Appointments:** Appointment management.
- **Prescriptions:** Prescription-related operations.
- **Laboratory:** Laboratory information management.
- **Security:** Security-related functionality.
- **AI Security:** AI/ML-based security analysis.
- **Audit:** Application activity and audit records.
- **Notifications:** Notification-related functionality.
- **API:** API endpoints and documentation.

## ⚙️ Run the Project Locally

### Prerequisites

Install the following:

- Python 3.11 or another version supported by the project's dependencies.
- Git.
- Visual Studio Code (recommended).

### Step 1: Clone the repository

```bash
git clone https://github.com/1si22ad012/AI_Based_Healthacre_Platform_WebApp.git
cd AI_Based_Healthacre_Platform_WebApp
```

### Step 2: Create a virtual environment

**Windows PowerShell:**

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can run the virtual environment's Python directly instead.

### Step 3: Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Configure environment variables

Create a `.env` file if the project's settings require one. Configure the required Django secret key, database settings, allowed hosts, and other environment-specific values.

**Important:** Never commit your real `.env` file, passwords, secret keys, or database credentials to GitHub.

### Step 5: Apply database migrations

```powershell
python manage.py migrate
```

### Step 6: Create an administrator account

```powershell
python manage.py createsuperuser
```

Follow the prompts to configure your username, email, and password.

### Step 7: Start the development server

```powershell
python manage.py runserver
```

Open the application:

- **Website:** http://127.0.0.1:8000/
- **Admin panel:** http://127.0.0.1:8000/admin/
- **Health check:** http://127.0.0.1:8000/healthz/
- **API documentation:** http://127.0.0.1:8000/api/docs/

The API documentation URL will work if the schema and Swagger routes are configured and accessible.

## 🚀 Deployment

The project is deployed using Render.

**Live URL:** https://ai-based-healthacre-platform-webapp.onrender.com/

The deployed application uses Daphne as its ASGI server.

A health-check endpoint is available at:

https://ai-based-healthacre-platform-webapp.onrender.com/healthz/

## 📂 Repository

GitHub: https://github.com/1si22ad012/AI_Based_Healthacre_Platform_WebApp

## 🔒 Security and Privacy

- Use synthetic patient information when testing or recording demonstrations.
- Never upload real patient records or personally identifiable medical information.
- Store secrets and credentials in environment variables.
- Enforce authorization checks before accessing protected healthcare records.
- Use HTTPS for deployed applications.
- Review encryption key management, database permissions, and audit logging before production use.

> This project is intended for educational and demonstration purposes. Production healthcare deployment requires appropriate security testing, privacy safeguards, and regulatory compliance.

## 🔮 Future Enhancements

- Improve real-time anomaly detection.
- Add enhanced security alerts and monitoring dashboards.
- Strengthen encryption key management.
- Expand automated security testing.
- Add comprehensive role-based permissions and reporting.
- Improve deployment monitoring and backup procedures.

## 👩‍💻 Author

**Deepthi U**

GitHub: [1si22ad012](https://github.com/1si22ad012)

## 📄 License

Add a license file if you intend to distribute or reuse this project publicly. Until then, no open-source license is specified.
