from django.test import TestCase

from security.services import aes_encrypt, aes_decrypt, ecc_generate_keypair, ecc_derive_shared_secret, ecc_sign, ecc_verify, rsa_generate_keypair, rsa_sign, rsa_verify
from security.key_management import ensure_active_key, rotate_key


class CryptoTests(TestCase):
    def test_aes_roundtrip(self):
        for size in (16, 24, 32):
            ct, nonce, tag, alg = aes_encrypt(b"secret medical data", "dev-v1", size)
            pt = aes_decrypt(ct, nonce, tag, "dev-v1", size)
            self.assertEqual(pt, b"secret medical data")

    def test_nonce_unique(self):
        n1 = aes_encrypt(b"a", "dev-v1", 32)[1]
        n2 = aes_encrypt(b"b", "dev-v1", 32)[1]
        self.assertNotEqual(n1, n2)

    def test_tampering_detected(self):
        ct, nonce, tag, alg = aes_encrypt(b"secret", "dev-v1", 32)
        tampered = bytearray(ct)
        if tampered:
            tampered[0] ^= 1
        with self.assertRaises(Exception):
            aes_decrypt(bytes(tampered), nonce, tag, "dev-v1", 32)

    def test_invalid_tag(self):
        ct, nonce, tag, alg = aes_encrypt(b"secret", "dev-v1", 32)
        bad_tag = bytes([x ^ 1 for x in tag])
        with self.assertRaises(Exception):
            aes_decrypt(ct, nonce, bad_tag, "dev-v1", 32)

    def test_ecc_shared_secret(self):
        priv1, pub1 = ecc_generate_keypair()
        priv2, pub2 = ecc_generate_keypair()
        s1 = ecc_derive_shared_secret(priv1, pub2)
        s2 = ecc_derive_shared_secret(priv2, pub1)
        self.assertEqual(s1, s2)

    def test_signature(self):
        priv, pub = ecc_generate_keypair()
        data = b"prescription canonical"
        sig = ecc_sign(priv, data)
        self.assertTrue(ecc_verify(pub, data, sig))
        self.assertFalse(ecc_verify(pub, b"tampered", sig))

    def test_rsa_signature(self):
        priv, pub = rsa_generate_keypair()
        data = b"rsa data"
        sig = rsa_sign(priv, data)
        self.assertTrue(rsa_verify(pub, data, sig))
        self.assertFalse(rsa_verify(pub, b"tampered", sig))

    def test_key_rotation(self):
        old = ensure_active_key("dev-v1-aes256", 32)
        new = rotate_key(old.version)
        self.assertNotEqual(old.version, new.version)
        self.assertEqual(new.status, "active")
