import base64
import hashlib
import hmac
import os
import secrets
import time
from typing import Tuple

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from django.conf import settings


class CryptoError(Exception):
    pass


def _master_secret() -> bytes:
    raw = getattr(settings, "ENCRYPTION_KEY_B64", "")
    if raw:
        try:
            key = base64.b64decode(raw, validate=True)
        except Exception as exc:
            raise CryptoError("Invalid ENCRYPTION_KEY_B64") from exc
        if len(key) < 32:
            raise CryptoError("ENCRYPTION_KEY_B64 must decode to at least 32 bytes")
        return key
    if settings.DEBUG or getattr(settings, "TESTING", False):
        # Stable development/test-only secret derived from SECRET_KEY. Documented as insecure for production.
        return hashlib.sha256(("dev-encryption:" + settings.SECRET_KEY).encode()).digest()
    raise CryptoError("ENCRYPTION_KEY_B64 is required in production")


def derive_key(version: str, key_size: int = 32) -> bytes:
    if key_size not in (16, 24, 32):
        raise CryptoError("Unsupported AES key size")
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=key_size,
        salt=version.encode("utf-8"),
        info=b"healthcare-aes-gcm-key",
    )
    return hkdf.derive(_master_secret())


def generate_nonce() -> bytes:
    return os.urandom(12)


def aes_encrypt(plaintext: bytes, version: str = "dev-v1", key_size: int = 32, aad: bytes = b"") -> Tuple[bytes, bytes, bytes, str]:
    key = derive_key(version, key_size)
    nonce = generate_nonce()
    aesgcm = AESGCM(key)
    ciphertext_with_tag = aesgcm.encrypt(nonce, plaintext, aad)
    # cryptography returns ciphertext + 16-byte tag.
    ciphertext = ciphertext_with_tag[:-16]
    tag = ciphertext_with_tag[-16:]
    algorithm = f"AES-{key_size * 8}-GCM"
    return ciphertext, nonce, tag, algorithm


def aes_decrypt(ciphertext: bytes, nonce: bytes, tag: bytes, version: str = "dev-v1", key_size: int = 32, aad: bytes = b"") -> bytes:
    key = derive_key(version, key_size)
    aesgcm = AESGCM(key)
    try:
        return aesgcm.decrypt(nonce, ciphertext + tag, aad)
    except InvalidTag as exc:
        raise CryptoError("Ciphertext authentication failed") from exc
    except Exception as exc:
        raise CryptoError("Decryption failed") from exc


def aes_key_size_from_algorithm(algorithm: str) -> int:
    # AES-128-GCM etc.
    if "128" in algorithm:
        return 16
    if "192" in algorithm:
        return 24
    return 32


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ECC ECDH
def ecc_generate_keypair() -> Tuple[str, str]:
    private_key = ec.generate_private_key(ec.SECP256R1())
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    return private_pem, public_pem


def ecc_derive_shared_secret(private_key_pem: str, peer_public_pem: str, key_size: int = 32) -> bytes:
    private_key = serialization.load_pem_private_key(private_key_pem.encode("utf-8"), password=None)
    peer_public = serialization.load_pem_public_key(peer_public_pem.encode("utf-8"))
    shared = private_key.exchange(ec.ECDH(), peer_public)
    hkdf = HKDF(algorithm=hashes.SHA256(), length=key_size, salt=None, info=b"healthcare-ecdh-hkdf")
    return hkdf.derive(shared)


def ecc_sign(private_key_pem: str, data: bytes) -> str:
    private_key = serialization.load_pem_private_key(private_key_pem.encode("utf-8"), password=None)
    signature = private_key.sign(data, ec.ECDSA(hashes.SHA256()))
    return base64.b64encode(signature).decode("ascii")


def ecc_verify(public_key_pem: str, data: bytes, signature_b64: str) -> bool:
    try:
        public_key = serialization.load_pem_public_key(public_key_pem.encode("utf-8"))
        signature = base64.b64decode(signature_b64, validate=True)
        public_key.verify(signature, data, ec.ECDSA(hashes.SHA256()))
        return True
    except Exception:
        return False


# RSA (optional supported asymmetric operations)
def rsa_generate_keypair() -> Tuple[str, str]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    return private_pem, public_pem


def rsa_sign(private_key_pem: str, data: bytes) -> str:
    private_key = serialization.load_pem_private_key(private_key_pem.encode("utf-8"), password=None)
    signature = private_key.sign(data, padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH), hashes.SHA256())
    return base64.b64encode(signature).decode("ascii")


def rsa_verify(public_key_pem: str, data: bytes, signature_b64: str) -> bool:
    try:
        public_key = serialization.load_pem_public_key(public_key_pem.encode("utf-8"))
        signature = base64.b64decode(signature_b64, validate=True)
        public_key.verify(signature, data, padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH), hashes.SHA256())
        return True
    except Exception:
        return False


def constant_time_compare(a: bytes, b: bytes) -> bool:
    return hmac.compare_digest(a, b)
