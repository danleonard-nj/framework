from typing import Any

from framework.auth.azure import AzureAdJwt
from framework.exceptions.authorization import (AuthorizationException,
                                                UnauthorizedException)
from framework.logger.providers import get_logger
from framework.validators.nulls import not_none, none_or_whitespace

logger = get_logger(__name__)


class AzureAd:
    def __init__(
        self,
        tenant: str,
        audiences: str,
        issuer: str
    ):
        self.__authorization_schemes = dict()
        self.__jwt_handler = AzureAdJwt(
            tenant_id=tenant,
            audiences=audiences,
            issuer=issuer)

    def validate_access_token(
            self,
            token: str,
            scheme: Any):
        '''
        Validate a service access token

        `token`: Bearer token string
        `scheme`: auth scheme
        '''

        not_none(scheme, 'scheme')
        not_none(token, 'token')

        payload = self.__validate_access_token_signature(
            token=token)

        logger.info(f'Validating authorization scheme: {scheme}')
        if not self.__validate_authorization(
                payload=payload,
                scheme=scheme):

            logger.info(f'Failed to validate authorization scheme')
            raise UnauthorizedException()
        return payload

    def add_authorization_policy(
        self,
        name,
        func
    ):
        self.__authorization_schemes[name] = func

    def __validate_access_token_signature(
        self,
        token
    ):
        return self.__jwt_handler.validate_token(
            token=token)

    def __validate_authorization(
        self,
        scheme,
        payload
    ):
        auth_func = self.__authorization_schemes.get(scheme)

        if not auth_func:
            raise AuthorizationException(
                f'No scheme with the name {scheme} is defined')

        return auth_func(payload)
