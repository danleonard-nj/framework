from framework.logger import get_logger
from framework.di.service_provider import ServiceProvider
import inspect

logger = get_logger(__name__)


class InternalProvider:
    service_provider = None

    @classmethod
    def bind(cls, service_provider):
        if cls.service_provider is None:
            cls.service_provider = service_provider
        logger.info('Bound service provider to internal provider')

    @classmethod
    def resolve(cls, _type):
        return cls.service_provider.resolve(
            _type=_type)
        
    @classmethod
    def get_provider(cls):
        return cls.service_provider


class ProviderBase:
    service_provider = None

    @classmethod
    def initialize_provider(cls):
        _ = cls.get_service_provider()

    @classmethod
    def configure_container(cls):
        pass

    @classmethod
    def get_service_provider(cls):
        if cls.service_provider is None:
            logger.info(f'Configuring base provider services')
            container = cls.configure_container()

            logger.info(f'Building service provider')
            service_provider = ServiceProvider(container)
            service_provider.build()

            cls.service_provider = service_provider

            # TODO: This replaces the application state
            InternalProvider.bind(
                service_provider=service_provider)

        return cls.service_provider


def get_function_args(func):
    return list(inspect.signature(func).parameters)



def inject_container_async(func):
    async def wrap(*args, **kwargs):
        func_args = get_function_args(func)

        if 'container' in func_args:
            logger.debug(f'Injecting service provider to view func: {func.__name__}')
            return await func(*args, **kwargs, container=InternalProvider.service_provider)
        return await func(*args, **kwargs)
    return wrap


def inject_container(func):
    def wrap(*args, **kwargs):
        func_args = get_function_args(func)

        if 'container' in func_args:
            logger.debug(f'Injecting service provider to view func: {func.__name__}')
            return func(*args, **kwargs, container=InternalProvider.service_provider)
        return func(*args, **kwargs)
    return wrap
