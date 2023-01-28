from typing import Any, Callable, Tuple

from framework.abstractions.abstract_request import RequestContextProvider
from framework.exceptions.authorization import UnauthorizedException
from framework.handlers.context import preserve_source_context
from framework.logger.providers import get_logger
from framework.utilities.object_utils import getattr_or_none
from jwt.exceptions import ExpiredSignatureError
from framework.serialization import Serializable

logger = get_logger(__name__)


def error_response(exception: Exception) -> Tuple[dict, int]:
    '''
    Return a response indicating an exception.  This is called any time
    an exception is thrown in the view method when it's wrapped by the
    response handler

    exception   :   thrown exception
    '''

    logger.debug('Invoking error response handler')

    data = {
        'error': exception.__class__.__name__,
        'message': str(exception),
    }

    if isinstance(exception, UnauthorizedException):
        logger.debug('Unauthorized')
        return data, 401
    if isinstance(exception, ExpiredSignatureError):
        logger.info('Token signature is expired')
        return data, 401
    else:
        # Don't return the traceback in the error response in production
        # if environment == Environment.Development:
        #     data['traceback'] = traceback.format_exc().split('\n')
        return data, 500


def __intercept_serializables(
    result
):
    '''
    Implicitly serialize objects implementing
    `Serializable` before creating response
    '''

    if isinstance(result, Serializable):
        logger.debug('Serializing response object implicitly')
        return result.to_dict()

    return result


def response_handler(func: Callable) -> Callable:
    '''
    Framework response handler
    '''

    async def wrapper(*args, **kwargs) -> Tuple[dict, int]:
        logger.debug('Response handler invoked')
        preserve_source_context(func=func)

        try:
            result = await func(*args, **kwargs)

            # Intercept responses that implement
            # Serializable and call to_dict()
            return __intercept_serializables(
                result=result)

        except Exception as ex:
            context = RequestContextProvider.get_request_context()
            logger.exception(f'Request {context.endpoint} failed: {str(ex)}')
            return error_response(ex)
    return wrapper


def error_handler(e):
    message = {'error': str(e)}
    return message, getattr_or_none(
        obj=e,
        name='code') or 500
