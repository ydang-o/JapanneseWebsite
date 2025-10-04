from __future__ import annotations
from typing import Tuple
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes

_private_key = None
_public_pem = None


def get_or_create_rsa_keys() -> Tuple[bytes, object]:
    global _private_key, _public_pem
    if _private_key is None:
        _private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = _private_key.public_key()
        _public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    return _public_pem, _private_key


def decrypt_payload(enc_bytes: bytes) -> bytes:
    _, priv = get_or_create_rsa_keys()
    return priv.decrypt(
        enc_bytes,
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
    )
