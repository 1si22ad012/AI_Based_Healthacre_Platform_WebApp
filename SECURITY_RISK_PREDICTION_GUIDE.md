# Security Risk Prediction Guide

## Service
`healthcare_ai/risk_history.py` aggregates SecurityEvent, AnomalyDetection, incidents per user over a configurable time window and computes an explainable 0-100 risk score with factors and trend.

## Dashboard
`/healthcare/risk-dashboard/` (admin only) shows top risk accounts.