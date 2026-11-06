import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib
import numpy as np
from django.conf import settings
from django.utils import timezone

from security.models import EncryptionOperation
from audit.models import AnomalyDetection, SecurityEvent, AnomalyAlert
from audit.services import create_audit_event, create_security_event, notify_user
from healthcare_ai.models import SecurityIncident
from healthcare_ai.services import calculate_risk_score

MODEL_DIR = Path(settings.ML_ARTIFACT_DIR)
POLICY_MODEL = "policy_random_forest.joblib"
IF_MODEL = "isolation_forest.joblib"
OCSVM_MODEL = "one_class_svm.joblib"
RF_ANOMALY_MODEL = "anomaly_random_forest.joblib"
MODEL_VERSION = "rf-policy-v1"
ANOMALY_MODEL_VERSION = "hybrid-anomaly-v1"

POLICY_LABELS = {
    0: ("standard", "AES-128-GCM", 16),
    1: ("strong", "AES-192-GCM", 24),
    2: ("high_security", "AES-256-GCM", 32),
    3: ("elevated_risk", "AES-256-GCM", 32),
}

SENSITIVITY_MAP = {"low": 0, "medium": 1, "high": 2, "critical": 3}
ROLE_MAP = {"patient": 0, "doctor": 1, "lab_tech": 2, "admin": 3, "administrator": 3}
RISK_MAP = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def _load(name: str):
    path = MODEL_DIR / name
    if not path.exists():
        return None
    try:
        return joblib.load(path)
    except Exception:
        return None


def _model_available(name: str) -> bool:
    return (MODEL_DIR / name).exists()


def normalize_policy_features(context: Dict[str, Any]) -> np.ndarray:
    sensitivity = SENSITIVITY_MAP.get(str(context.get("sensitivity", "high")).lower(), 2)
    role = ROLE_MAP.get(str(context.get("role", "doctor")).lower(), 1)
    file_size_kb = float(context.get("file_size_kb", context.get("file_size", 0)) or 0) / 1024.0 if "file_size" in context and "file_size_kb" not in context else float(context.get("file_size_kb", 0) or 0)
    cpu = float(context.get("cpu_utilization", 0.0) or 0.0)
    latency = float(context.get("network_latency", 0.0) or 0.0)
    recent_events = float(context.get("recent_security_events", 0) or 0)
    anomaly_score = float(context.get("anomaly_score", 0.0) or 0.0)
    access_frequency = float(context.get("access_frequency", 0) or 0)
    risk = RISK_MAP.get(str(context.get("risk_level", "medium")).lower(), 1)
    return np.array([[sensitivity, role, file_size_kb, cpu, latency, recent_events, anomaly_score, access_frequency, risk]], dtype=float)


def select_policy(context: Dict[str, Any]) -> Dict[str, Any]:
    start = time.perf_counter()
    fallback_used = False
    model_recommendation = None
    model_confidence = None
    model_version = MODEL_VERSION if _model_available(POLICY_MODEL) else "unavailable"

    # Mandatory security rules first.
    sensitivity = str(context.get("sensitivity", "high")).lower()
    risk_level = str(context.get("risk_level", "medium")).lower()
    anomaly_score = float(context.get("anomaly_score", 0.0) or 0.0)
    recent_events = int(context.get("recent_security_events", 0) or 0)

    mandatory_elevated = (
        risk_level == "critical"
        or anomaly_score >= 0.85
        or recent_events >= 8
    )
    mandatory_minimum = 2 if sensitivity in ("high", "critical") else 1 if sensitivity == "medium" else 0

    # Model inference
    model_label = None
    if not mandatory_elevated:
        model = _load(POLICY_MODEL)
        if model is not None:
            try:
                X = normalize_policy_features(context)
                proba = model.predict_proba(X)[0]
                model_label = int(model.predict(X)[0])
                model_confidence = float(np.max(proba))
                model_recommendation = POLICY_LABELS.get(model_label, (None, None, None))[0]
                if model_confidence < 0.55:
                    fallback_used = True
                    model_label = None
            except Exception:
                fallback_used = True
                model_label = None
        else:
            fallback_used = True

    if mandatory_elevated:
        final_label = 3
        rationale = "Mandatory security rule selected elevated risk due to critical sensitivity, high risk, anomaly score, or repeated security events."
    elif model_label is None:
        final_label = max(mandatory_minimum, 2)
        rationale = "Safe fallback policy selected because the model was unavailable, invalid, or uncertain."
        fallback_used = True
    else:
        final_label = max(model_label, mandatory_minimum)
        if final_label != model_label:
            rationale = "Model recommendation was raised to satisfy mandatory security rules."
        else:
            rationale = "Random Forest policy model recommendation accepted."

    policy_name, algorithm, key_size = POLICY_LABELS[final_label]
    allowed = final_label != 3
    duration_ms = (time.perf_counter() - start) * 1000.0

    result = {
        "policy": policy_name,
        "model_recommendation": model_recommendation,
        "model_confidence": model_confidence,
        "model_version": model_version,
        "risk_category": "elevated" if final_label == 3 else "high" if final_label == 2 else "medium" if final_label == 1 else "low",
        "algorithm": algorithm,
        "key_size": key_size,
        "allowed": allowed,
        "fallback_used": fallback_used,
        "rationale": rationale,
        "duration_ms": round(duration_ms, 3),
        "timestamp": timezone.now().isoformat(),
    }
    return result


ANOMALY_FEATURES = [
    "failed_logins", "login_frequency", "unusual_hour", "denied_requests",
    "upload_size_kb", "record_access_count", "cpu_utilization",
    "encryption_failures", "invalid_tags", "suspicious_params",
]


def normalize_anomaly_features(context: Dict[str, Any]) -> np.ndarray:
    vals = []
    for key in ANOMALY_FEATURES:
        v = context.get(key, 0)
        try:
            vals.append(float(v))
        except (TypeError, ValueError):
            vals.append(0.0)
    return np.array([vals], dtype=float)


def detect_anomaly(context: Dict[str, Any]) -> Dict[str, Any]:
    fallback_used = False
    detector_results = {}
    scores = []
    model_available = _model_available(IF_MODEL) and _model_available(OCSVM_MODEL)

    if model_available:
        try:
            X = normalize_anomaly_features(context)
            if_model = _load(IF_MODEL)
            oc_model = _load(OCSVM_MODEL)
            rf_model = _load(RF_ANOMALY_MODEL)

            if_score = float(if_model.decision_function(X)[0])
            if_pred = int(if_model.predict(X)[0])  # 1 normal, -1 anomaly
            detector_results["isolation_forest"] = {
                "prediction": "normal" if if_pred == 1 else "anomaly",
                "score": if_score,
            }
            scores.append(0.0 if if_pred == 1 else 1.0)

            oc_pred = int(oc_model.predict(X)[0])
            detector_results["one_class_svm"] = {
                "prediction": "normal" if oc_pred == 1 else "anomaly",
                "score": float(oc_model.decision_function(X)[0]),
            }
            scores.append(0.0 if oc_pred == 1 else 1.0)

            if rf_model is not None:
                rf_proba = float(rf_model.predict_proba(X)[0][1]) if hasattr(rf_model, "predict_proba") else float(rf_model.predict(X)[0])
                detector_results["random_forest"] = {
                    "prediction": "attack" if rf_proba >= 0.5 else "normal",
                    "score": rf_proba,
                }
                scores.append(rf_proba)
        except Exception:
            model_available = False
            fallback_used = True

    if not model_available:
        fallback_used = True
        # Conservative deterministic fallback, clearly not model inference.
        failed = float(context.get("failed_logins", 0) or 0)
        denied = float(context.get("denied_requests", 0) or 0)
        invalid_tags = float(context.get("invalid_tags", 0) or 0)
        score = min(1.0, (failed / 10.0) + (denied / 10.0) + (invalid_tags / 3.0))
        is_anomaly = score >= 0.5
        detector_results["rule_based_fallback"] = {
            "prediction": "anomaly" if is_anomaly else "normal",
            "score": score,
        }
        scores = [score]

    combined_score = float(np.mean(scores)) if scores else 0.0
    is_anomaly = combined_score >= 0.5
    return {
        "is_anomaly": is_anomaly,
        "score": round(combined_score, 4),
        "threshold": 0.5,
        "detectors": detector_results,
        "model_available": model_available,
        "fallback_used": fallback_used,
        "model_version": ANOMALY_MODEL_VERSION,
    }


ANOMALY_FEATURE_NAMES = list(ANOMALY_FEATURES)


def extract_security_features(context: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and normalize anomaly features. Never includes sensitive payloads."""
    features = {}
    for key in ANOMALY_FEATURES:
        raw = context.get(key, 0)
        try:
            if key in ("unusual_hour",):
                features[key] = 1 if bool(raw) or str(raw).lower() in {"1", "true", "yes"} else 0
            else:
                features[key] = float(raw)
        except (TypeError, ValueError):
            features[key] = 0.0
    # Clamp negatives
    for key, value in list(features.items()):
        if isinstance(value, float) and value < 0:
            features[key] = 0.0
    return features


def _detector_prediction(detectors: Dict[str, Any], name: str) -> str:
    entry = detectors.get(name, {})
    return str(entry.get("prediction", ""))


def _detector_score(detectors: Dict[str, Any], name: str) -> float:
    entry = detectors.get(name, {})
    try:
        return float(entry.get("score", 0.0) or 0.0)
    except (TypeError, ValueError):
        return 0.0


def persist_anomaly_detection(context, result, actor=None, request=None, event_type="security_activity"):
    """Persist anomaly detection result, creating event/alert/incident as appropriate. Returns AnomalyDetection."""
    from django.db import transaction

    features = extract_security_features(context if isinstance(context, dict) else {})
    is_anomaly = bool(result.get("is_anomaly", False))
    combined_score = float(result.get("score", 0.0) or 0.0)
    detectors = result.get("detectors", {}) or {}
    risk_features = {
        "failed_logins": int(features.get("failed_logins", 0) or 0),
        "denied_requests": int(features.get("denied_requests", 0) or 0),
        "invalid_tags": int(features.get("invalid_tags", 0) or 0),
        "unusual_hour": bool(features.get("unusual_hour", 0)),
        "anomaly": is_anomaly,
    }
    risk = calculate_risk_score(risk_features)

    # Dedup: skip if identical anomaly recorded in last 60s for same actor
    dedup_key = f"anomaly-dedup:{getattr(actor, 'id', None)}:{round(combined_score, 3)}:{is_anomaly}"
    from django.core.cache import cache

    if is_anomaly and cache.get(dedup_key):
        return None
    if is_anomaly:
        cache.set(dedup_key, True, 60)

    security_event = None
    anomaly_alert = None
    security_incident = None

    with transaction.atomic():
        if is_anomaly:
            security_event = create_security_event(
                "anomaly",
                actor=actor,
                request=request,
                metadata={"features": features, "detector": "hybrid", "score": combined_score},
                severity="high" if combined_score >= 0.7 else "medium",
                risk_score=combined_score,
            )
            anomaly_alert = AnomalyAlert.objects.create(
                security_event=security_event,
                detector="hybrid",
                score=combined_score,
                threshold=float(result.get("threshold", 0.5) or 0.5),
                status="open",
            )
            security_incident = None
            for inc in SecurityIncident.objects.all().order_by("-created_at")[:20]:
                if security_event.id in (inc.related_events or []):
                    security_incident = inc
                    break
            # notify admins for high risk
            if risk["level"] in ("high", "critical"):
                try:
                    from accounts.models import User

                    for admin_user in (User.objects.filter(role="admin") | User.objects.filter(is_superuser=True)):
                        notify_user(
                            admin_user,
                            "Anomaly detected",
                            f"Suspicious activity detected (score {combined_score}). Review required.",
                            category="security",
                            url="/security/ai-monitoring/",
                        )
                except Exception:
                    pass
        else:
            # Record normal detection as low-severity security event only when explicitly requested? Skip to avoid noise.
            pass

        detection = AnomalyDetection.objects.create(
            actor=actor,
            user_role=getattr(actor, "role", "") if actor else "",
            event_type=event_type,
            detector="hybrid",
            model_version=result.get("model_version", ANOMALY_MODEL_VERSION),
            input_features=features,
            isolation_forest_prediction=_detector_prediction(detectors, "isolation_forest"),
            isolation_forest_score=_detector_score(detectors, "isolation_forest"),
            one_class_svm_prediction=_detector_prediction(detectors, "one_class_svm"),
            one_class_svm_score=_detector_score(detectors, "one_class_svm"),
            random_forest_prediction=_detector_prediction(detectors, "random_forest"),
            random_forest_score=_detector_score(detectors, "random_forest"),
            combined_score=combined_score,
            threshold=float(result.get("threshold", 0.5) or 0.5),
            is_anomaly=is_anomaly,
            risk_score=risk["score"],
            risk_level=risk["level"],
            reasons=risk.get("reasons", []),
            action_taken="blocked" if (is_anomaly and event_type == "record_create") else ("recorded" if is_anomaly else "allowed"),
            detection_status="open" if is_anomaly else "closed",
            security_event=security_event,
            anomaly_alert=anomaly_alert,
            security_incident=security_incident,
        )

        if security_event:
            create_audit_event(
                "anomaly.detected",
                actor=actor,
                target_type="AnomalyDetection",
                target_id=detection.id,
                request=request,
                result="success",
                severity="high" if is_anomaly else "info",
                details={"score": combined_score, "risk_level": risk["level"], "event_type": event_type},
            )
        return detection
