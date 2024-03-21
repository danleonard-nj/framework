import base64
import json

import requests
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
from framework.caching import MemoryCache
from framework.exceptions.nulls import ArgumentNullException
from framework.logger.providers import get_logger
from framework.utilities.iter_utils import first

logger = get_logger('framework.autorization')


class AzureJwksKeyException(Exception):
    def __init__(self, message):
        super().__init__(message)


class AzureJwksProvider:
    ''' 
    Provider for JWKS web token signing used 
    to verify bearer token provieded to the
    client 
    '''

    def __init__(
        self,
        tenant_id: str
    ):
        self._tenant_id = tenant_id
        self._cache = MemoryCache()

        ArgumentNullException.if_none_or_whitespace(tenant_id, 'tenant_id')

    def _ensure_bytes(
        self,
        key
    ):
        if isinstance(key, str):
            key = key.encode('utf-8')
        return key

    def _decode_value(
        self,
        val: bytes
    ) -> int:
        decoded = base64.urlsafe_b64decode(self._ensure_bytes(val) + b'==')
        return int.from_bytes(decoded, 'big')

    def _rsa_pem_from_jwk(
        self,
        jwk: str
    ) -> bytes:
        '''
        Decode the PEM data from the token signing keys
        to use to verify
        '''

        return RSAPublicNumbers(
            n=self._decode_value(jwk['n']),
            e=self._decode_value(jwk['e'])
        ).public_key(default_backend()).public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo)

    def _get_token_kid(
        self,
        token
    ) -> str:
        '''
        Get the KID from the provided token metadata
        '''
        encoded = token.split('.')[0].encode()
        decoded = base64.b64decode(encoded).decode()
        kid = json.loads(decoded).get('kid')
        return kid

    def _get_azure_jwks(
        self
    ):
        cached = self._cache.get(
            key=f'{self.__class__.__name__}-jwks-discovery')

        if cached is not None:
            return cached

        response = requests.get(
            url=f'https://login.microsoftonline.com/{self._tenant_id}/discovery/v2.0/keys')

        data = response.json()
        keys = data.get('keys')

        self._cache.set(
            key=f'{self.__class__.__name__}-jwks-discovery',
            value=keys,
            ttl=60 * 60 * 24)

        return keys

    def get_jwks_by_token_kid(
        self,
        token: str
    ) -> bytes:
        '''
        Get the required signigng key tokn tyoe fo
        a particular tokrn
        '''
        kid = self._get_token_kid(
            token=token)
        jwks_keys = self._get_azure_jwks()

        key = first(
            items=jwks_keys,
            func=lambda x: x.get('kid') == kid)

        if key is None:
            raise AzureJwksKeyException(
                f"No key set exists for key with the ID '{kid}'")

        rsa_pem = self._rsa_pem_from_jwk(
            jwk=key)
        return rsa_pem
