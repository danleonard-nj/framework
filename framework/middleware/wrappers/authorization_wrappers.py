from functools import wraps
from typing import Callable, List, Union
from flask import request

from framework.middleware.helpers import get_bearer
from framework.logger.providers import get_logger
from framework.application.state import get_state
from framework.exceptions.authorization import UnauthorizedException
from framework.middleware.authorization import AuthMiddleware
from framework.constants.constants import InclusionType
from framework.validators.nulls import not_none

from framework.dependency_injection.container import Container

logger = get_logger(__name__)


def authorization(scheme: Union[List[str], str], inclusion_type: Union[InclusionType, None] = None) -> Callable:
    '''
    Authorization scheme decorator

    scheme              :   list or string declaring the required scheme
    inclusion_type      :   indicate if all schemes must be satisfied or if
                            any can be verified
    '''

    def real_decorator(function) -> Callable:
        @wraps(function)
        def wrapper(*args, **kwargs) -> Callable:
            container = get_state(Container)
            auth_middleware: AuthMiddleware = container.resolve(AuthMiddleware)

            is_valid = auth_middleware.validate_access_token(
                token=get_bearer(),
                scheme=scheme,
                inclusion_type=inclusion_type)
            if not is_valid:
                raise UnauthorizedException()
            return function(*args, **kwargs)
        return wrapper
    return real_decorator


def api_key(name: str):
    def real_decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            not_none(name, 'name')
            container = get_state(Container)
            auth_middleware: AuthMiddleware = container.resolve(AuthMiddleware)

            api_key = auth_middleware.get_api_key(
                name=name)

            provided_key = request.headers.get(
                auth_middleware.api_key_header or 'api-key')

            if not provided_key:
                logger.info('Unauthorized: No API key provided')
                raise UnauthorizedException('API key is required')

            if provided_key != api_key:
                logger.info('Unauthorized: Invalid API key provided')
                raise UnauthorizedException('API key is not valid')

            return function(*args, **kwargs)
        return wrapper
    return real_decorator
