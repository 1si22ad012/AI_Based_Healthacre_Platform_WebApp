import os
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.svm import OneClassSVM

from django.conf import settings

from .services import MODEL_DIR, POLICY_MODEL, IF_MODEL, OCSVM_MODEL, RF_ANOMALY_MODEL

MODEL_DIR.mkdir(parents=True, exist_ok=True)


def train_policy_model() -> str:
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

    # Label rules with some noise.
    y = np.zeros(n, dtype=int)
    for i in range(n):
        if risk[i] >= 3 or anomaly_score[i] >= 0.85 or recent_events[i] >= 8:
            y[i] = 3
        elif sensitivity[i] >= 2 or risk[i] >= 2 or anomaly_score[i] >= 0.6 or sensitivity[i] >= 3:
            y[i] = 2
        elif sensitivity[i] >= 1 or risk[i] >= 1 or file_size_kb[i] > 2000:
            y[i] = 1
        else:
            y[i] = 0
    # Add mild noise to a small subset.
    noise_idx = rng.choice(n, size=int(n * 0.03), replace=False)
    y[noise_idx] = rng.integers(0, 4, size=len(noise_idx))

    model = RandomForestClassifier(n_estimators=150, random_state=42, class_weight="balanced")
    model.fit(X, y)
    joblib.dump(model, MODEL_DIR / POLICY_MODEL)
    return str(MODEL_DIR / POLICY_MODEL)


def train_anomaly_models() -> dict:
    rng = np.random.default_rng(7)
    n_normal = 3000
    n_attack = 600

    def normal_rows(n):
        base = np.column_stack([
            rng.poisson(1, n),          # failed_logins
            rng.poisson(5, n),          # login_frequency
            rng.integers(0, 2, n),      # unusual_hour
            rng.poisson(0, n),          # denied_requests
            rng.normal(200, 50, n),     # upload_size_kb
            rng.poisson(10, n),         # record_access_count
            rng.normal(30, 10, n),      # cpu_utilization
            rng.poisson(0, n),          # encryption_failures
            rng.poisson(0, n),          # invalid_tags
            rng.poisson(0, n),          # suspicious_params
        ])
        # Include low-activity development traffic as normal so that missing or
        # low CPU, small uploads, and first-record access are not false positives.
        low = np.column_stack([
            np.zeros(int(n * 0.35)),
            rng.poisson(2, int(n * 0.35)),
            np.zeros(int(n * 0.35)),
            np.zeros(int(n * 0.35)),
            rng.uniform(0, 20, int(n * 0.35)),
            rng.poisson(1, int(n * 0.35)),
            np.zeros(int(n * 0.35)),
            np.zeros(int(n * 0.35)),
            np.zeros(int(n * 0.35)),
            np.zeros(int(n * 0.35)),
        ])
        return np.vstack([base, low])

    def attack_rows(n):
        return np.column_stack([
            rng.poisson(8, n),
            rng.poisson(20, n),
            rng.integers(1, 2, n),
            rng.poisson(6, n),
            rng.normal(2000, 500, n),
            rng.poisson(40, n),
            rng.normal(85, 10, n),
            rng.poisson(3, n),
            rng.poisson(2, n),
            rng.poisson(4, n),
        ])

    X_normal = normal_rows(n_normal)
    X_attack = attack_rows(n_attack)
    X_all = np.vstack([X_normal, X_attack])
    y_all = np.concatenate([np.zeros(len(X_normal)), np.ones(len(X_attack))])

    iso = IsolationForest(contamination=0.1, random_state=42)
    iso.fit(X_normal)
    joblib.dump(iso, MODEL_DIR / IF_MODEL)

    oc = OneClassSVM(nu=0.1, kernel="rbf", gamma="scale")
    oc.fit(X_normal)
    joblib.dump(oc, MODEL_DIR / OCSVM_MODEL)

    rf = RandomForestClassifier(n_estimators=100, random_state=42, class_weight="balanced")
    rf.fit(X_all, y_all)
    joblib.dump(rf, MODEL_DIR / RF_ANOMALY_MODEL)

    return {
        "isolation_forest": str(MODEL_DIR / IF_MODEL),
        "one_class_svm": str(MODEL_DIR / OCSVM_MODEL),
        "random_forest": str(MODEL_DIR / RF_ANOMALY_MODEL),
    }
