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
        self._authorization_schemes = dict()
        self._jwt_handler = AzureAdJwt(
            tenant_id=tenant,
            audiences=audiences,
            issuer=issuer)

    def validate_access_token(
            self,
            token: str,
            scheme: Any):
        '''
        Validate a service access token

        `token`: The access token to validate
        `scheme`: The name of the authorization scheme to validate
        '''

        ArgumentNullException.if_none_or_empty(scheme, 'scheme')
        ArgumentNullException.if_none_or_empty(token, 'token')

        payload = self._validate_access_token_signature(
            token=token)

        logger.debug(f'Validating authorization scheme: {scheme}')
        if not self._validate_authorization(
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
        Define an authorization policy function.  The function
        takes a single parameter, the decoded access token payload.

        `name`: name of the authorization policy
        `func`: the authorization policy function
        '''

        self._authorization_schemes[name] = func

    def _validate_access_token_signature(
        self,
        token: str
    ):
        '''
        Validate the access token signature

        `token`: the access token to validate
        '''

        return self._jwt_handler.verify_token_signing_and_decode(
            token=token)

    def _validate_authorization(
        self,
        scheme: str,
        payload: Dict
    ):
        '''
        Validate the authorization scheme

        `scheme`: name of authorization scheme to validate
        `payload`: decoded access token payload
        '''

        auth_func = self._authorization_schemes.get(scheme)

        if not auth_func:
            raise AuthorizationException(
                f'No scheme with the name {scheme} is defined')

        return auth_func(payload)
