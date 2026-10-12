import base64

from cryptography.fernet import Fernet
from flask import current_app


def _fernet() -> Fernet:
    key = current_app.config["AES_SECRET_KEY"].encode("utf-8")
    # Derive 32-url-safe base64 key from configured secret
    fkey = base64.urlsafe_b64encode(key[:32].ljust(32, b"0"))
    return Fernet(fkey)


def encrypt_value(plain: str) -> str:
    if not plain:
        return ""
    return _fernet().encrypt(plain.encode("utf-8")).decode("utf-8")


def decrypt_value(token: str) -> str:
    if not token:
        return ""
    return _fernet().decrypt(token.encode("utf-8")).decode("utf-8")
