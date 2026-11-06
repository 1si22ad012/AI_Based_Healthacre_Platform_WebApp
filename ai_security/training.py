import json
import os
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.metrics import (accuracy_score, classification_report, confusion_matrix,
                            f1_score, precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import train_test_split
from sklearn.svm import OneClassSVM

from django.conf import settings

from .services import (MODEL_DIR, POLICY_MODEL, IF_MODEL, OCSVM_MODEL,
                       RF_ANOMALY_MODEL, ANOMALY_FEATURES)

MODEL_DIR.mkdir(parents=True, exist_ok=True)
REGISTRY_FILE = MODEL_DIR / "model_registry.json"


def _dataset_source():
    path = os.environ.get("SECURITY_DATASET_PATH", "")
    if path and Path(path).exists():
        return path
    return "synthetic (ai_security/training.py)"


def _load_dataset():
    path = os.environ.get("SECURITY_DATASET_PATH", "")
    if path and Path(path).exists():
        import csv

        rows = []
        labels = []
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                try:
                    feat = [float(r[col]) for col in ANOMALY_FEATURES]
                    lab = int(float(r.get("label", 0)))
                except (KeyError, ValueError, TypeError):
                    continue
                rows.append(feat)
                labels.append(lab)
        if rows:
            return np.array(rows), np.array(labels), path
    return None, None, None


def train_policy_model() -> dict:
    rng = np.random.default_rng(42)
    n = 4000
    sensitivity = rng.integers(0, 4, size=n)
    role = rng.integers(0, 4, size=n)
    file_size_kb = rng.exponential(500, size=n)
    cpu = rng.uniform(0, 100, size=n)
    latency = rng.uniform(0, 300, size=n)
    recent_events = rng.poisson(1, size=n)
    anomaly_score = rng.uniform(0, 1, size=n)
    access_frequency = rng.poisson(3, size=n)
    risk = rng.integers(0, 4, size=n)

    X = np.column_stack([sensitivity, role, file_size_kb, cpu, latency, recent_events, anomaly_score, access_frequency, risk])
    y = np.zeros(n, dtype=int)
    for i in range(n):
        if risk[i] >= 3 or anomaly_score[i] >= 0.85 or recent_events[i] >= 8:
            y[i] = 3
        elif sensitivity[i] >= 2 or risk[i] >= 2 or anomaly_score[i] >= 0.6:
            y[i] = 2
        elif sensitivity[i] >= 1 or risk[i] >= 1 or file_size_kb[i] > 2000:
            y[i] = 1
        else:
            y[i] = 0
    noise_idx = rng.choice(n, size=int(n * 0.03), replace=False)
    y[noise_idx] = rng.integers(0, 4, size=len(noise_idx))

    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)
    model = RandomForestClassifier(n_estimators=150, random_state=42, class_weight="balanced")
    model.fit(Xtr, ytr)
    pred = model.predict(Xte)
    metrics = {
        "accuracy": float(accuracy_score(yte, pred)),
        "precision_macro": float(precision_score(yte, pred, average="macro", zero_division=0)),
        "recall_macro": float(recall_score(yte, pred, average="macro", zero_division=0)),
        "f1_macro": float(f1_score(yte, pred, average="macro", zero_division=0)),
        "confusion_matrix": confusion_matrix(yte, pred).tolist(),
    }
    joblib.dump(model, MODEL_DIR / POLICY_MODEL)
    return {"model": str(MODEL_DIR / POLICY_MODEL), "metrics": metrics, "dataset": "synthetic", "samples": n}


def train_anomaly_models() -> dict:
    X, y, src = _load_dataset()
    if X is None:
        rng = np.random.default_rng(7)
        n_normal = 3000
        n_attack = 600

        def normal_rows(n):
            base = np.column_stack([
                rng.poisson(1, n), rng.poisson(5, n), rng.integers(0, 2, n), rng.poisson(0, n),
                rng.normal(200, 50, n), rng.poisson(10, n), rng.normal(30, 10, n),
                rng.poisson(0, n), rng.poisson(0, n), rng.poisson(0, n),
            ])
            low = np.column_stack([
                np.zeros(int(n * 0.35)), rng.poisson(2, int(n * 0.35)), np.zeros(int(n * 0.35)),
                np.zeros(int(n * 0.35)), rng.uniform(0, 20, int(n * 0.35)), rng.poisson(1, int(n * 0.35)),
                np.zeros(int(n * 0.35)), np.zeros(int(n * 0.35)), np.zeros(int(n * 0.35)), np.zeros(int(n * 0.35)),
            ])
            return np.vstack([base, low])

        def attack_rows(n):
            return np.column_stack([
                rng.poisson(8, n), rng.poisson(20, n), rng.integers(1, 2, n), rng.poisson(6, n),
                rng.normal(2000, 500, n), rng.poisson(40, n), rng.normal(85, 10, n),
                rng.poisson(3, n), rng.poisson(2, n), rng.poisson(4, n),
            ])

        X_normal = normal_rows(n_normal)
        X_attack = attack_rows(n_attack)
        X = np.vstack([X_normal, X_attack])
        y = np.concatenate([np.zeros(len(X_normal)), np.ones(len(X_attack))])
        src = "synthetic (ai_security/training.py)"
    else:
        pass

    # Split
    try:
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)
    except Exception:
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3, random_state=42)

    # Unsupervised models trained on normal-only
    normal_mask = (ytr == 0)
    Xtr_normal = Xtr[normal_mask] if normal_mask.any() else Xtr

    iso = IsolationForest(contamination=0.1, random_state=42)
    iso.fit(Xtr_normal)
    joblib.dump(iso, MODEL_DIR / IF_MODEL)

    oc = OneClassSVM(nu=0.1, kernel="rbf", gamma="scale")
    oc.fit(Xtr_normal)
    joblib.dump(oc, MODEL_DIR / OCSVM_MODEL)

    rf = RandomForestClassifier(n_estimators=100, random_state=42, class_weight="balanced")
    rf.fit(Xtr, ytr)
    joblib.dump(rf, MODEL_DIR / RF_ANOMALY_MODEL)

    # Evaluation on held-out test set
    def eval_supervised(model, Xte, yte):
        pred = model.predict(Xte)
        proba = model.predict_proba(Xte)[:, 1] if hasattr(model, "predict_proba") else pred
        try:
            auc = float(roc_auc_score(yte, proba))
        except Exception:
            auc = None
        return {
            "accuracy": float(accuracy_score(yte, pred)),
            "precision": float(precision_score(yte, pred, zero_division=0)),
            "recall": float(recall_score(yte, pred, zero_division=0)),
            "f1": float(f1_score(yte, pred, zero_division=0)),
            "roc_auc": auc,
            "confusion_matrix": confusion_matrix(yte, pred).tolist(),
            "false_positive_rate": float(((pred == 1) & (yte == 0)).sum() / max((yte == 0).sum(), 1)),
            "false_negative_rate": float(((pred == 0) & (yte == 1)).sum() / max((yte == 1).sum(), 1)),
        }

    iso_pred = (iso.predict(Xte) == -1).astype(int)
    oc_pred = (oc.predict(Xte) == -1).astype(int)
    rf_metrics = eval_supervised(rf, Xte, yte)

    try:
        iso_auc = float(roc_auc_score(yte, -iso.decision_function(Xte)))
    except Exception:
        iso_auc = None
    try:
        oc_auc = float(roc_auc_score(yte, -oc.decision_function(Xte)))
    except Exception:
        oc_auc = None

    metrics = {
        "isolation_forest": {
            "accuracy": float(accuracy_score(yte, iso_pred)),
            "precision": float(precision_score(yte, iso_pred, zero_division=0)),
            "recall": float(recall_score(yte, iso_pred, zero_division=0)),
            "f1": float(f1_score(yte, iso_pred, zero_division=0)),
            "roc_auc": iso_auc,
            "confusion_matrix": confusion_matrix(yte, iso_pred).tolist(),
            "false_positive_rate": float(((iso_pred == 1) & (yte == 0)).sum() / max((yte == 0).sum(), 1)),
            "false_negative_rate": float(((iso_pred == 0) & (yte == 1)).sum() / max((yte == 1).sum(), 1)),
        },
        "one_class_svm": {
            "accuracy": float(accuracy_score(yte, oc_pred)),
            "precision": float(precision_score(yte, oc_pred, zero_division=0)),
            "recall": float(recall_score(yte, oc_pred, zero_division=0)),
            "f1": float(f1_score(yte, oc_pred, zero_division=0)),
            "roc_auc": oc_auc,
            "confusion_matrix": confusion_matrix(yte, oc_pred).tolist(),
            "false_positive_rate": float(((oc_pred == 1) & (yte == 0)).sum() / max((yte == 0).sum(), 1)),
            "false_negative_rate": float(((oc_pred == 0) & (yte == 1)).sum() / max((yte == 1).sum(), 1)),
        },
        "random_forest": rf_metrics,
        "classification_report": classification_report(yte, rf.predict(Xte), zero_division=0, output_dict=True),
    }

    version = datetime.utcnow().strftime("anomaly-%Y%m%d%H%M%S")
    registry = {
        "version": version,
        "training_timestamp": datetime.utcnow().isoformat(),
        "dataset_source": src,
        "feature_schema": ANOMALY_FEATURES,
        "metrics": metrics,
        "model_files": {
            "isolation_forest": str(MODEL_DIR / IF_MODEL),
            "one_class_svm": str(MODEL_DIR / OCSVM_MODEL),
            "random_forest": str(MODEL_DIR / RF_ANOMALY_MODEL),
        },
    }
    REGISTRY_FILE.write_text(json.dumps(registry, indent=2))
    return {"models": [str(MODEL_DIR / IF_MODEL), str(MODEL_DIR / OCSVM_MODEL), str(MODEL_DIR / RF_ANOMALY_MODEL)], "metrics": metrics, "version": version, "dataset": src}