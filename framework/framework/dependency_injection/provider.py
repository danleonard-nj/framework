import inspect

from framework.application.state import bind_state
from framework.logger.providers import get_logger

logger = get_logger(__name__)


class InternalProvider:
    container = None

    @classmethod
    def bind(cls, container):
        if cls.container is None:
            cls.container = container

    @classmethod
    def resolve(cls, _type):
        return cls.container.resolve(
            _type=_type)


class ProviderBase:
    container = None

    @classmethod
    def initialize_provider(cls):
        _ = cls.get_container()

    @classmethod
    def configure_container(cls):
        pass

    @classmethod
    def get_container(cls):
        if cls.container is None:
            container = cls.configure_container()
            bind_state(container)
            cls.container = container

            # TODO: This replaces the application state
            InternalProvider.bind(
                container=container)

        return cls.container


def get_function_args(func):
    return list(inspect.signature(func).parameters)


def inject_container_async(func):
    async def wrap(*args, **kwargs):
        func_args = get_function_args(func)

        if 'container' in func_args:
            return await func(*args, **kwargs, container=InternalProvider.container)
        return await func(*args, **kwargs)
    return wrap


def inject_container(func):
    def wrap(*args, **kwargs):
        func_args = get_function_args(func)

        if 'container' in func_args:
            return func(*args, **kwargs, container=InternalProvider.container)
        return func(*args, **kwargs)
    return wrap
