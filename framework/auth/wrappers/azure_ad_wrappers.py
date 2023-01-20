from functools import wraps
from typing import Any, Callable

from deprecated import deprecated
from quart import request

from framework.abstractions.abstract_request import RequestContextProvider
from framework.auth.azure import AzureAd
from framework.di.static_provider import InternalProvider
from framework.exceptions.authorization import (AuthorizationHeaderException,
                                                UnauthorizedException)
from framework.exceptions.rest import RequestHeaderException
from framework.logger.providers import get_logger
from framework.validators.nulls import none_or_whitespace

AUTH_HEADER = 'Authorization'

logger = get_logger(__name__)


@deprecated
def get_bearer() -> str:
    context = RequestContextProvider.get_request_context()
    authorization_header = context.headers.get(
        'Authorization')

    if (authorization_header or '') != '':
        return authorization_header.split(' ')[1]
    else:
        raise UnauthorizedException()


def get_bearer() -> str:
    if AUTH_HEADER not in request.headers:
        RequestHeaderException(
            header=AUTH_HEADER)

    authorization_header = request.headers.get(
        AUTH_HEADER)

    if none_or_whitespace(authorization_header):
        logger.debug(f'Invalid auth token: {authorization_header}')
        raise AuthorizationHeaderException()
    else:
        return authorization_header.split(' ')[1]


def azure_ad_authorization(scheme: str) -> Callable:
    '''
    Use the provided auth scheme definition to authorize
    requests on the route.

    `scheme`: name of the auth scheme (defined in service
    config))
    '''
    def decorator(function: Callable) -> Callable:
        @wraps(function)
        async def wrapper(*args, **kwargs) -> Any:
            auth_handler = InternalProvider.resolve(
                _type=AzureAd)

            token = get_bearer()
            auth_handler.validate_access_token(
                token=token,
                scheme=scheme)
            return await function(*args, **kwargs)
        return wrapper
    return decorator
