from functools import wraps
from typing import Any, Callable

from framework.abstractions.abstract_request import RequestContextProvider
from framework.auth.azure import AzureAd
from framework.dependency_injection.provider import InternalProvider
from framework.exceptions.authorization import UnauthorizedException
from framework.logger.providers import get_logger

logger = get_logger(__name__)


def get_bearer() -> str:
    context = RequestContextProvider.get_request_context()
    authorization_header = context.headers.get(
        'Authorization')

    if (authorization_header or '') != '':
        return authorization_header.split(' ')[1]
    else:
        raise UnauthorizedException()


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
