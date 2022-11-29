import base64
import hashlib


def md5(data: str):
    hashed_bytes = hashlib.md5(data.encode()).digest()
    return base64.b64encode(hashed_bytes).decode()


def sha256(data: str):
    hash_bytes = hashlib.sha256(data.encode()).digest()
    return base64.b64encode(hash_bytes).decode()
