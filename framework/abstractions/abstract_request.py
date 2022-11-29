from abc import ABC
from flask import Request as FlaskRequest
from quart import Request as QuartRequest
from flask import request as flask_request
from quart import request as quart_request
import inspect

from flask import Flask
from framework.logger.providers import get_logger

logger = get_logger(__name__)


class RequestContextProviderException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class AbstractRequest(ABC, FlaskRequest, QuartRequest):
    pass


class RequestContextProvider:
    AbstractServerType = None
    Initialized = False

    @classmethod
    def initialize_provider(cls, app):
        # Discern the abstract server type (flask or quart)
        cls.AbstractServerType = app.__class__.__name__.lower()
        cls.Initialized = True

    @classmethod
    def get_request_context(cls):
        if not cls.Initialized:
            raise RequestContextProviderException(
                'The provider is not initialized')

        logger.info(f'Abstract server type: {cls.AbstractServerType}')
        _globals = inspect.currentframe().f_globals

        _request = _globals.get(f'{cls.AbstractServerType}_request')
        logger.info(f'Request context: {_request}')

        return _request
