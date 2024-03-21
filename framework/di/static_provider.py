import inspect

from framework.di.service_provider import ServiceProvider
from framework.logger import get_logger

logger = get_logger(__name__)


class InternalProvider:
    service_provider = None

    @classmethod
    def bind(
        cls,
        service_provider
    ):
        '''
        Binds a service provider to the internal provider.
        '''

        if cls.service_provider is None:
            cls.service_provider = service_provider
        logger.info('Bound service provider to internal provider')

    @classmethod
    def resolve(
        cls,
        _type: type
    ):
        '''
        Resolves a service for a given type.

        `_type`: The type for which to resolve the service.
        '''

        return cls.service_provider.resolve(_type=_type)

    @classmethod
    def get_provider(
        cls
    ):
        '''
        Returns the service provider.
        '''

        return cls.service_provider


class ProviderBase:
    '''
    A base class for providers.
    '''

    service_provider = None

    @classmethod
    def initialize_provider(
        cls
    ):
        '''
        Initializes the service provider.
        '''

        _ = cls.get_service_provider()

    @classmethod
    def configure_container(
        cls
    ):
        '''
        Configures the container. To be implemented by subclasses.
        '''

        pass

    @classmethod
    def get_service_provider(
        cls
    ):
        '''
        Returns the service provider, building it if necessary.
        '''

        if cls.service_provider is None:
            container = cls.configure_container()

            # Build the service provider
            service_provider = ServiceProvider(container)
            service_provider.build()

            cls.service_provider = service_provider

            # Bind the service provider to the internal provider
            InternalProvider.bind(
                service_provider=service_provider)

        return cls.service_provider


def get_function_args(func):
    '''
    Returns the arguments of a function.

    `func`: The function for which to return the arguments.
    '''

    return list(inspect.signature(func).parameters)


def inject_container_async(func):
    '''
    Asynchronously injects the container into a function if it requires it.

    `func`: The function to wrap.
    '''

    async def wrap(*args, **kwargs):
        func_args = get_function_args(func)

        # If the function has a container argument, inject the provider
        if 'container' in func_args:

            return await func(*args,
                              **kwargs,
                              container=InternalProvider.service_provider)

        return await func(*args, **kwargs)

    return wrap


def inject_container(func):
    '''
    Injects the container into a function if it requires it.

    `func`: The function to wrap.
    '''

    def wrap(*args, **kwargs):
        func_args = get_function_args(func)

        # If the function has a container argument, inject the provider
        if 'container' in func_args:

            return func(*args,
                        **kwargs,
                        container=InternalProvider.service_provider)

        return func(*args, **kwargs)

    return wrap
