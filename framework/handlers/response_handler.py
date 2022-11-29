from functools import wraps
from typing import Any, Callable, Tuple

from framework.abstractions.abstract_request import RequestContextProvider
from framework.application.state import get_state
from framework.configuration.configuration import Configuration
from framework.constants.constants import ConfigurationKey
from framework.exceptions.authorization import UnauthorizedException
from framework.logger.providers import get_logger
from framework.utilities.object_utils import getattr_or_none
from jwt.exceptions import ExpiredSignatureError
from deprecated import deprecated

logger = get_logger(__name__)
configuration = get_state(Configuration)
environment = configuration.app_environment


@deprecated
def is_diagnostics_enabled():
    return (configuration.diagnostics.get(
        ConfigurationKey.DIAGNOSTIC_RESPONSE_ENABLED)
        or False)


@deprecated
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


@deprecated
def status_response(data: dict, status_code: int = 200):
    '''
    Generic status code response returned by the handler

    data            :   the respone body
    status_code     :   the status code
    '''

    return data, status_code


@deprecated
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


@deprecated
def handle_response(func):
    try:
        response = func()

        if isinstance(response, tuple):
            if len(response) != 2:
                logger.info('Invalid length for response tuple')
                raise Exception(
                    "Type of 'tuple' as view function response must have a length of 2")
            if not isinstance(response[0], dict):
                logger.info("Response tuple data is not of type 'dict'")
                raise Exception("Response data must be of type 'dict'")
            if not isinstance(response[1], int):
                logger.info("Response tuple status code is not of type 'int'")
                raise Exception("Response status code must be of type 'int'")

            return status_response(
                data=response[0],
                status_code=response[1])

        if isinstance(response, dict):
            return status_response(
                data=response)
    except Exception as ex:
        _request = RequestContextProvider.get_request_context()
        logger.exception(f'Request {_request.endpoint} failed')
        return error_response(ex)


@deprecated
def response_handler(function: Callable) -> Callable:
    '''
    Response handler decorator

    function    :   wrapped view function
    '''

    @wraps(function)
    def wrapper(*args, **kwargs) -> Tuple[dict, int]:
        def invoke_response(): return function(*args, **kwargs)
        return handle_response(invoke_response)
    return wrapper


@deprecated
def error_handler(e):
    message = {'error': str(e)}
    return message, getattr_or_none(
        obj=e,
        name='code') or 500
