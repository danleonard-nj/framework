from typing import Callable, Tuple

from deprecated import deprecated
from pydantic import BaseModel
from framework.abstractions.abstract_request import RequestContextProvider
from framework.exceptions.authorization import UnauthorizedException
from framework.exceptions.rest import HttpException
from framework.handlers.context import preserve_source_context
from framework.logger.providers import get_logger
from framework.serialization import Serializable
from framework.utilities.object_utils import getattr_or_none
from jwt.exceptions import ExpiredSignatureError

logger = get_logger(__name__)


def _get_error_response(exception: Exception) -> Tuple[dict, int]:
    '''
    Return a response indicating an exception.  This is called any time
    an exception is thrown in the view method when it's wrapped by the
    response handler

    exception   :   thrown exception
    '''

    data = {
        'error': exception.__class__.__name__,
        'message': str(exception),
    }

    if isinstance(exception, HttpException):
        return data, exception.status_code

    if isinstance(exception, (UnauthorizedException, ExpiredSignatureError)):
        return data, 401

    return data, 500


def _intercept_serializables(
    result
):
    '''
    Implicitly serialize objects implementing
    `Serializable` before creating response
    '''

    if isinstance(result, Serializable):
        logger.debug('Serializing Serializable object response implicitly')
        return result.to_dict()

    if isinstance(result, BaseModel):
        logger.debug('Serializing Pydantic object response implicitly')
        return result.model_dump()

    return result


def response_handler(func: Callable) -> Callable:
    '''
    Framework response handler
    '''

    async def wrapper(*args, **kwargs) -> Tuple[dict, int]:
        preserve_source_context(func=func)

        try:
            result = await func(*args, **kwargs)

            # Intercept responses that implement
            # Serializable and call to_dict()
            return _intercept_serializables(
                result=result)

        except Exception as ex:
            context = RequestContextProvider.get_request_context()
            logger.exception(f'Request {context.endpoint} failed: {str(ex)}')
            return _get_error_response(ex)
    return wrapper


@deprecated
def error_handler(e):
    message = {'error': str(e)}
    return message, getattr_or_none(
        obj=e,
        name='code') or 500
