from threading import Lock
from typing import Dict
import time


class CacheValue:
    def __init__(self, value, ttl):
        self.value = value
        self.ttl = ttl
        self.timestamp = time.time()
        self.expiration = self.timestamp + self.ttl

    def is_expired(self):
        return self.timestamp + self.ttl < time.time()

    def remaining_ttl(self):
        return time.time() - self.timestamp + self.ttl


class MemoryCache:
    lock = Lock()
    cache: Dict[str, CacheValue] = dict()

    def get(self, key):
        cached = self.cache.get(key)

        # Return none for an undefined key
        if cached is None:
            return cached

        # Return none for an expired key
        if cached.is_expired():
            del self.cache[key]

            return None

        return cached.value

    def set(self, key, value, ttl):
        self.lock.acquire()

        self.cache[key] = CacheValue(
            value=value,
            ttl=ttl)

        self.lock.release()
