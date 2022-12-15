from functools import wraps
from typing import Callable, Dict

from framework.abstractions.abstract_request import RequestContextProvider
from framework.configuration import Configuration
from framework.di.static_provider import InternalProvider
from framework.exceptions.authorization import UnauthorizedException
from framework.exceptions.nulls import NullArgumentException
from framework.logger import get_logger
from framework.validators.nulls import none_or_whitespace

logger = get_logger(__name__)


class ApiKeyNotFoundException(Exception):
    def __init__(self, key_name, *args: object) -> None:
        super().__init__(
            f"No key with the name '{key_name}' is defined")


class InvalidApiKeyConfigurationException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(
            f"Key configuration section is not valid")


def get_key_definitions(
    configuration: Configuration
) -> Dict:
    NullArgumentException.if_none(configuration, 'configuration')

    api_keys = configuration.auth.get('api_keys', dict())
    return api_keys.get('keys')


def get_header_key(
    configuration: Configuration
) -> str:
    NullArgumentException.if_none(configuration, 'configuration')

    api_keys = configuration.auth.get('api_keys', dict())
    return api_keys.get('header')


def key_authorization(name: str):
    def real_decorator(function: Callable):
        @wraps(function)
        async def wrapper(*args, **kwargs):
            configuration = InternalProvider.resolve(Configuration)

            # Get the key definitions from app config
            key_definitions = get_key_definitions(
                configuration=configuration)

            if key_definitions is None:
                raise InvalidApiKeyConfigurationException()
            source_api_key = key_definitions.get(name)

            if none_or_whitespace(source_api_key):
                raise ApiKeyNotFoundException(
                    key_name=name)

            # Name of the header containing the key
            header_key = get_header_key(
                configuration=configuration)

            context = RequestContextProvider.get_request_context()
            request_api_key = context.headers.get(header_key)

            if none_or_whitespace(request_api_key):
                logger.info(f"No key found on header '{header_key}'")
                raise UnauthorizedException()

            logger.info(f"Key: {request_api_key}")

            if request_api_key != source_api_key:
                logger.info(f"Value for key '{request_api_key}' is not valid")
                raise UnauthorizedException()

            return await function(*args, **kwargs)
        return wrapper
    return real_decorator
