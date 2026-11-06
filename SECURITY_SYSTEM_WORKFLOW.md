# Security System Workflow

User Login → OTP Verification → Role-Based Dashboard
    ↓
Medical Record Creation
    ↓
Feature Extraction (10 attributes)
    ↓
Anomaly Detection (IF + OCSVM + RF)
    ↓
Hybrid Decision (combined_score >= 0.5)
    ↓
Security Risk Scoring (0-100)
    ↓
SecurityEvent (if anomaly)
    ↓
AnomalyAlert + SecurityIncident
    ↓
Admin Notification + WebSocket
    ↓
Administrator Investigation (acknowledge/investigate/resolve/false positive)
    ↓
Audit Log (hash-chained)

Key rotation: Admin → /security/key-management/ → rotate → new active key + retired old key + audit event. Existing records remain decryptable via stored key_version.