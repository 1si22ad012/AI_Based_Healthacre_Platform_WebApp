# Security Key Management Guide

## Overview
Encryption keys are never stored in plaintext. Only `KeyMetadata` records are persisted, containing safe metadata (key ID, version, algorithm, status, fingerprint, timestamps, usage count, rotation history). Actual key material is derived at runtime using HKDF from a master secret configured via `ENCRYPTION_KEY_B64` (or a dev-only derived secret in DEBUG).

## Key Generation
- `security/key_management.py:ensure_active_key` creates or reactivates a `KeyMetadata` row for a given version.
- Key material is derived in `security/services.py:derive_key` using HKDF-SHA256 with the version as salt and `info=b"healthcare-aes-gcm-key"`.
- Master secret source: `ENCRYPTION_KEY_B64` env var (production) or dev fallback (DEBUG only).

## Key Rotation
- `security/key_management.py:rotate_key` marks the old key as `rotated`, sets `rotated_at`, appends to `rotation_history`, creates a new active key with a timestamp-based version, and records `KeyActivity` entries.
- Rotation is admin-only via `/security/key-management/` with confirmation.
- An audit event `key.rotate` is recorded.

## Existing Data Compatibility
- Old keys are not deleted or invalidated; their metadata remains with status `rotated`.
- Records store `key_version`, so decryption uses the original key version.
- `ensure_active_key` never overwrites existing metadata; it backfills missing fields.

## Production Requirements
- Set `ENCRYPTION_KEY_B64` to a 32+ byte secret from a KMS/HSM.
- Use Redis channel layer for multi-process realtime.
- Enforce admin-only access (views check `is_admin`).
- Never log key material; `check_email_config`-style diagnostics expose only booleans.