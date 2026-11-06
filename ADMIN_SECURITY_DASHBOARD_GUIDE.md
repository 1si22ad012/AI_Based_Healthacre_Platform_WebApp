# Admin Security Dashboard Guide

## URL
Administrator dashboard: `/` (after login as admin). Detailed pages: `/security/ai-monitoring/`, `/security/anomaly-history/`, `/security/incidents/`, `/security/key-management/`, `/security/model-information/`, `/healthcare/risk-dashboard/`.

## Data Sources
- SecurityEvent, AnomalyDetection, AnomalyAlert, SecurityIncident, KeyMetadata, EncryptionOperation.
- Aggregation service: `audit/services.py:admin_analytics(days)`.

## Charts
- Anomaly trend (line): daily normal vs anomalous.
- Normal vs anomalous (doughnut).
- Security events by type (bar).
- Risk distribution (bar): low 0-24, medium 25-49, high 50-74, critical 75-100.

## Risk Score Calculation
Uses existing `calculate_risk_score` (0-100, weighted factors). Distribution uses AnomalyDetection.risk_score.

## Testing
`python manage.py test accounts.test_admin_dashboard`