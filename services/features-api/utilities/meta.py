from functools import wraps
from typing import Callable, List

from framework.auth.wrappers.azure_ad_wrappers import azure_ad_authorization
from framework.di.static_provider import inject_container_async
from framework.handlers.response_handler_async import response_handler
from quart import Blueprint

from domain.exceptions import ArgumentNullException
from utilities.api_key import key_authorization


class MetaBlueprint(Blueprint):
    def __get_endpoint(
        self,
        view_function: Callable
    ) -> str:
        ''' Get the endpoint name for route '''
        return f'__route__{view_function.__name__}'

    def with_key_auth(
        self,
        rule: str,
        methods: List[str],
        key_name: str
    ):
        '''
        Register a route with API key authorization
        '''

        ArgumentNullException.if_none_or_whitespace(rule, 'rule')
        ArgumentNullException.if_none_or_whitespace(key_name, 'key_name')
        ArgumentNullException.if_none_or_empty(methods, 'methods')

        def decorator(function):
            @self.route(rule, methods=methods, endpoint=self.__get_endpoint(function))
            @response_handler
            @key_authorization(name=key_name)
            @inject_container_async
            @wraps(function)
            async def wrapper(*args, **kwargs):
                return await function(*args, **kwargs)
            return wrapper
        return decorator

    def configure(self,  rule: str, methods: List[str], auth_scheme: str):
        def decorator(function):
            @self.route(rule, methods=methods, endpoint=self.__get_endpoint(function))
            @response_handler
            @azure_ad_authorization(scheme=auth_scheme)
            @inject_container_async
            @wraps(function)
            async def wrapper(*args, **kwargs):
                return await function(*args, **kwargs)
            return wrapper
        return decorator
