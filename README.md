# AI-Based Security for Healthcare Applications

A full-stack Django healthcare platform with adaptive AES-GCM encryption, ECC key exchange, digital signatures, AI policy selection, anomaly detection, audit logging, WebSockets, and role-based dashboards.

## Setup (Windows PowerShell)

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py check
python manage.py makemigrations
python manage.py migrate
python manage.py shell -c "from accounts.models import User; User.objects.create_superuser('admin@example.com','AdminPass123!Secure',first_name='Admin',last_name='User')"
python manage.py train_security_models
python manage.py test
python manage.py runserver
```

Open http://127.0.0.1:8000/

## Demo users

Create via Django admin or registration. Sample credentials if created manually:
- admin@example.com / AdminPass123!Secure
- doctor@example.com / DoctorPass123!Secure
- patient@example.com / PatientPass123!Secure
- lab@example.com / LabPass123!Secure

## Real-time

WebSockets are served at ws://127.0.0.1:8000/ws/security/. The default channel layer is in-memory for local development. For multi-process deployment, set REDIS_URL and use channels_redis.

## Tests

```powershell
python manage.py test
```

## Notes

- Development encryption uses a key derived from SECRET_KEY when ENCRYPTION_KEY_B64 is empty. Set ENCRYPTION_KEY_B64 for production.
- ML models are trained on synthetic data only.
- Media files are served only through authorized download views in production configuration.

## Render Deployment

### Build Command
```text
pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate --noinput
```

### Start Command
```text
daphne -b 0.0.0.0 -p $PORT config.asgi:application
```

### Required Environment Variables
- `SECRET_KEY`
- `DEBUG=False`
- `ALLOWED_HOSTS=.onrender.com`
- `CSRF_TRUSTED_ORIGINS=https://your-app.onrender.com`
- `DATABASE_URL`
- `REDIS_URL`
- `ENCRYPTION_KEY_B64`
- `ENCRYPTION_KEY_VERSION=prod-v1`

### Encryption Key Backup
Generate once and store securely:
```powershell
python -c "import base64,os; print(base64.b64encode(os.urandom(32)).decode())"
```
Back up this value outside the repository. If it changes, existing encrypted records cannot be decrypted.

### Create Demo Admin
```powershell
python manage.py createsuperuser
```
Or use Django shell. Create safe demo accounts with strong passwords and synthetic data only.
