import base64
import hashlib


def md5(
    data: str
) -> str:
    hashed_bytes = hashlib.md5(data.encode()).digest()
    return base64.b64encode(hashed_bytes).decode()


def sha256(
    data: str,

) -> str:
    hash_bytes = hashlib.sha256(data.encode()).digest()
    return base64.b64encode(hash_bytes).decode()


def sha3_256(
    data: str
) -> str:
    hash_bytes = hashlib.sha3_256(data.encode()).digest()
    return base64.b64encode(hash_bytes).decode()


def sha3_224(
    data: str
) -> str:
    hash_bytes = hashlib.sha224(data.encode()).digest()
    return base64.b64encode(hash_bytes).decode()


def sha3_512(
    data: str
) -> str:
    hash_bytes = hashlib.sha512(data.encode()).digest()
    return base64.b64encode(hash_bytes).decode()


def sha1(
    data: str
) -> str:
    hash_bytes = hashlib.sha1(data.encode()).digest()
    return base64.b64encode(hash_bytes).decode()
