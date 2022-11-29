
from typing import TypeVar


T = TypeVar('T')


def getattr_or_none(obj, name):
    if hasattr(obj, name):
        return getattr(obj, name)
    return None
