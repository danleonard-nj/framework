import base64
import json

import requests
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
from framework.caching import MemoryCache
from framework.logger.providers import get_logger
from framework.utilities.pinq import first

logger = get_logger(__name__)


class AzureJwksProvider:
    def __init__(self, tenant_id):
        self.__tenant_id = tenant_id
        self.__cache = MemoryCache()

    def __ensure_bytes(
        self,
        key
    ):
        if isinstance(key, str):
            key = key.encode('utf-8')
        return key

    def __decode_value(
        self,
        val
    ):
        decoded = base64.urlsafe_b64decode(self.__ensure_bytes(val) + b'==')
        return int.from_bytes(decoded, 'big')

    def __rsa_pem_from_jwk(
        self,
        jwk
    ):
        return RSAPublicNumbers(
            n=self.__decode_value(jwk['n']),
            e=self.__decode_value(jwk['e'])
        ).public_key(default_backend()).public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo)

    def __get_token_kid(
        self,
        token
    ) -> str:
        encoded = token.split('.')[0].encode()
        decoded = base64.b64decode(encoded).decode()
        kid = json.loads(decoded).get('kid')
        return kid

    def __get_azure_jwks(
        self
    ):
        cached = self.__cache.get(
            key=f'{self.__class__.__name__}-jwks-discovery')

        if cached is not None:
            return cached

        response = requests.get(
            url=f'https://login.microsoftonline.com/{self.__tenant_id}/discovery/v2.0/keys')

        data = response.json()
        keys = data.get('keys')

        self.__cache.set(
            key=f'{self.__class__.__name__}-jwks-discovery',
            value=keys,
            ttl=60 * 60 * 24)

        return keys

    def get_jwks_by_token_kid(
        self,
        token
    ) -> bytes:
        kid = self.__get_token_kid(
            token=token)
        jwks_keys = self.__get_azure_jwks()

        key = first(
            items=jwks_keys,
            func=lambda x: x.get('kid') == kid)

        if key is None:
            raise Exception(f"No key set exists for key with the ID '{kid}'")

        rsa_pem = self.__rsa_pem_from_jwk(
            jwk=key)
        return rsa_pem
