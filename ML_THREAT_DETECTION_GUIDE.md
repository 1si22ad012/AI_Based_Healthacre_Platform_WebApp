# ML Threat Detection Guide

## Models
Isolation Forest, One-Class SVM, Random Forest (unchanged algorithms).

## Training
`python manage.py train_security_models` trains on synthetic data by default, or on a CSV at SECURITY_DATASET_PATH with the 10 feature columns + label.

## Evaluation
Real metrics computed on a held-out test set: accuracy, precision, recall, F1, ROC-AUC, confusion matrix, false-positive/negative rates. Stored in ml_artifacts/model_registry.json.

## Versioning
Model registry records version, timestamp, dataset source, feature schema, metrics. Do not auto-activate unverified models.