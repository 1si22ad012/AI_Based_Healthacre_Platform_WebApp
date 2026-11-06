# Anomaly Feature Attributes

Exact features from `ai_security/services.py:ANOMALY_FEATURES`:

| # | Attribute | Meaning | Type | Collection |
|---|---|---|---|---|
| 1 | failed_logins | Failed login count for actor | int | User.failed_login_count |
| 2 | login_frequency | Recent suspicious security events in last hour | int | SecurityEvent count |
| 3 | unusual_hour | 1 if activity outside 06:00-22:00 | int (0/1) | timezone check |
| 4 | denied_requests | Denied request count | int | request context |
| 5 | upload_size_kb | Upload size in KB | float | content length |
| 6 | record_access_count | Records for patient | int | MedicalRecord count |
| 7 | cpu_utilization | CPU utilization | float | request context |
| 8 | encryption_failures | Failed encryption ops for user | int | EncryptionOperation count |
| 9 | invalid_tags | Invalid AES-GCM tag count | int | request context |
| 10 | suspicious_params | Suspicious parameter count | int | request context |

All three models (Isolation Forest, One-Class SVM, Random Forest) use the same 10 features. No patient medical content is sent to models.