import base64
import hashlib


def md5(data: str) -> str:
    """
    Calculate the MD5 hash of the input data.

    Args:
        data (str): The input data to be hashed.

    Returns:
        str: The MD5 hash of the input data, encoded as a base64 string.
    """
    hashed_bytes = hashlib.md5(data.encode()).digest()
    return base64.b64encode(hashed_bytes).decode()


def sha256(data: str) -> str:
    """
    Calculate the SHA256 hash of the input data.

    Args:
        data (str): The input data to be hashed.

    Returns:
        str: The SHA256 hash of the input data, encoded as a base64 string.
    """
    hash_bytes = hashlib.sha256(data.encode()).digest()
    return base64.b64encode(hash_bytes).decode()


def sha3_256(data: str) -> str:
    """
    Calculate the SHA3-256 hash of the input data.

    Args:
        data (str): The input data to be hashed.

    Returns:
        str: The SHA3-256 hash of the input data, encoded as a base64 string.
    """
    hash_bytes = hashlib.sha3_256(data.encode()).digest()
    return base64.b64encode(hash_bytes).decode()


def sha3_224(data: str) -> str:
    """
    Calculate the SHA3-224 hash of the input data.

    Args:
        data (str): The input data to be hashed.

    Returns:
        str: The SHA3-224 hash of the input data, encoded as a base64 string.
    """
    hash_bytes = hashlib.sha224(data.encode()).digest()
    return base64.b64encode(hash_bytes).decode()


def sha3_512(data: str) -> str:
    """
    Calculate the SHA3-512 hash of the input data.

    Args:
        data (str): The input data to be hashed.

    Returns:
        str: The SHA3-512 hash of the input data, encoded as a base64 string.
    """
    hash_bytes = hashlib.sha512(data.encode()).digest()
    return base64.b64encode(hash_bytes).decode()


def sha1(data: str) -> str:
    """
    Calculate the SHA1 hash of the input data.

    Args:
        data (str): The input data to be hashed.

    Returns:
        str: The SHA1 hash of the input data, encoded as a base64 string.
    """
    hash_bytes = hashlib.sha1(data.encode()).digest()
    return base64.b64encode(hash_bytes).decode()
