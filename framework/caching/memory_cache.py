import time
from threading import Lock
from typing import Any


class CacheValue:
    def __init__(
        self,
        value: Any,
        ttl: int
    ):
        self.value = value
        self.ttl = ttl
        self.timestamp = time.time()
        self.expiration = self.timestamp + self.ttl

    def is_expired(
        self
    ) -> bool:
        return self.timestamp + self.ttl < time.time()

    def remaining_ttl(
        self
    ) -> float:
        return time.time() - self.timestamp + self.ttl


class MemoryCache:
    lock = Lock()
    cache: dict[str, CacheValue] = dict()

    def get(
        self,
        key: str
    ) -> Any:
        '''
        Retrieves the value associated with the given key from the cache.

        `key` (str): The key to retrieve the value for.

        Returns the value associated with the key, or None if the key is
        undefined or expired.
        '''

        cached = self.cache.get(key)

        # Return none for an undefined key
        if cached is None:
            return cached

        # Return none for an expired key
        if cached.is_expired():
            del self.cache[key]

            return None

        return cached.value

    def set(
        self,
        key: str,
        value: Any,
        ttl: int
    ):
        '''
        Sets a key-value pair in the cache with a specified time-to-live (ttl).

        `key`: The key to set in the cache.
        `value`: The value to associate with the key.
        `ttl`: The time-to-live (in seconds) for the key-value pair.
        '''

        self.lock.acquire()

        self.cache[key] = CacheValue(
            value=value,
            ttl=ttl)

        self.lock.release()
