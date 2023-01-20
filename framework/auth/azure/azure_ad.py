from typing import Any, Callable, Dict

from framework.auth.azure import AzureAdJwt
from framework.exceptions.authorization import (AuthorizationException,
                                                UnauthorizedException)
from framework.exceptions.nulls import ArgumentNullException
from framework.logger.providers import get_logger

logger = get_logger('framework.authorization')


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
        '''

        ArgumentNullException.if_none_or_empty(scheme, 'scheme')
        ArgumentNullException.if_none_or_empty(token, 'token')

        payload = self.__validate_access_token_signature(
            token=token)

        logger.debug(f'Validating authorization scheme: {scheme}')
        if not self.__validate_authorization(
                payload=payload,
                scheme=scheme):

            logger.debug(f'Failed to validate authorization scheme: {scheme}')
            raise UnauthorizedException()
        return payload

    def add_authorization_policy(
        self,
        name: str,
        func: Callable
    ):
        '''
        Define an authorization policy function
        '''

        self.__authorization_schemes[name] = func

    def __validate_access_token_signature(
        self,
        token: str
    ):
        '''
        Validate the access token signature
        '''

        return self.__jwt_handler.verify_token_signing_and_decode(
            token=token)

    def __validate_authorization(
        self,
        scheme: str,
        payload: Dict
    ):
        auth_func = self.__authorization_schemes.get(scheme)

        if not auth_func:
            raise AuthorizationException(
                f'No scheme with the name {scheme} is defined')

        return auth_func(payload)
