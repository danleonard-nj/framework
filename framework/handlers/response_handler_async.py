from typing import Any, Callable, Tuple

from framework.abstractions.abstract_request import RequestContextProvider
from framework.exceptions.authorization import UnauthorizedException
from framework.handlers.context import preserve_source_context
from framework.logger.providers import get_logger
from framework.utilities.object_utils import getattr_or_none
from jwt.exceptions import ExpiredSignatureError

logger = get_logger(__name__)


def error_response(exception: Exception) -> Tuple[dict, int]:
    '''
    Return a response indicating an exception.  This is called any time
    an exception is thrown in the view method when it's wrapped by the
    response handler

    exception   :   thrown exception
    '''

    logger.exception(
        f'Invoking error response: {exception.__class__.__name__}')

    data = {
        'error': exception.__class__.__name__,
        'message': str(exception),
    }

    if isinstance(exception, UnauthorizedException):
        logger.info('Unauthorized')
        return data, 401
    if isinstance(exception, ExpiredSignatureError):
        logger.info('Token signature is expired')
        return data, 401
    else:
        # Don't return the traceback in the error response in production
        # if environment == Environment.Development:
        #     data['traceback'] = traceback.format_exc().split('\n')
        return data, 500


def status_response(data: dict, status_code: int = 200):
    '''
    Generic status code response returned by the handler

    data            :   the respone body
    status_code     :   the status code
    '''

    return data, status_code


def validate_response(response: Any) -> None:
    '''
    Validate the respone is of the right type to avoid an unhandled exception
    in the response handler.  Often this is raised if the view function returns
    the standard tuple instead of a dict:

    invalid: {
        'data' : response
    }, 200

    response    :   the response body
    '''

    if not isinstance(response, [dict, tuple]):
        raise Exception(
            f'Invalid response type from view function: {type(response)}')


async def handle_response(
    func: Callable
) -> Any:
    try:
        return await func()
    except Exception as ex:
        context = RequestContextProvider.get_request_context()
        logger.exception(f'Request {context.endpoint} failed: {str(ex)}')
        return error_response(ex)


def response_handler(func: Callable) -> Callable:
    '''
    Response handler decorator

    function    :   wrapped view function
    '''

    async def wrapper(*args, **kwargs) -> Tuple[dict, int]:
        logger.debug('Response handler invoked')
        preserve_source_context(func=func)

        try:
            return await func(*args, **kwargs)

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
