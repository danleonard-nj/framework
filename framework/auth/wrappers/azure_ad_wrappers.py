from functools import wraps
from typing import Any, Callable

from framework.auth.azure import AzureAd
from framework.di.static_provider import InternalProvider
from framework.exceptions.authorization import AuthorizationHeaderException
from framework.exceptions.rest import RequestHeaderException
from framework.logger.providers import get_logger
from framework.validators.nulls import none_or_whitespace
from quart import request

AUTHORIZATION_HEADER_NAME = 'Authorization'

logger = get_logger(__name__)


def get_bearer() -> str:
    '''
    Retrieves the bearer token from the authorization header.
    '''

    if AUTHORIZATION_HEADER_NAME not in request.headers:
        RequestHeaderException(
            header=AUTHORIZATION_HEADER_NAME)

    authorization_header = request.headers.get(
        AUTHORIZATION_HEADER_NAME)

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
