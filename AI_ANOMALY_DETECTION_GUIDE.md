# AI Anomaly Detection Guide

## Algorithms
1. **Isolation Forest** (`ml_artifacts/isolation_forest.joblib`) — unsupervised; trained on normal-only synthetic data; contamination=0.1.
2. **One-Class SVM** (`one_class_svm.joblib`) — unsupervised RBF; nu=0.1; trained on normal-only data.
3. **Random Forest** (`anomaly_random_forest.joblib`) — supervised; trained on normal + attack synthetic data; balanced classes.

## Feature Extraction
Centralized in `ai_security/services.py:extract_security_features`, validated and normalized. Features are the 10 `ANOMALY_FEATURES`.

## Hybrid Decision
- Each model produces a prediction and score.
- Binary scores (0 normal / 1 anomaly) are averaged; RF contributes its attack probability.
- `combined_score >= 0.5` → anomaly.
- Rule-based fallback if models unavailable.

## Persistence
`persist_anomaly_detection` creates `SecurityEvent` (high), `AnomalyAlert`, `SecurityIncident` (via create_security_event), notifies admins for high/critical risk, records `AnomalyDetection` and audit event. Dedup via 60s cache key.

## Scores vs Risk
- Anomaly score: model-derived 0–1.
- Risk score: deterministic 0–100 from `calculate_risk_score`.
- These are not interchangeable.