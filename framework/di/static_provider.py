import inspect
import threading  # Added for thread safety
from framework.di.service_provider import ServiceProvider
from framework.logger import get_logger

logger = get_logger(__name__)


def get_current_container():
    """
    Returns the current container.
    If in a Flask/Quart request, create (or return) and use a scoped container;
    otherwise, return the root provider.
    """
    try:
        from flask import has_request_context, g
        if has_request_context():
            if not hasattr(g, 'di_container'):
                # Create a new scope for the current request
                g.di_container = InternalProvider.get_provider().create_scope()
            return g.di_container
    except ImportError:
        # Flask not available; fallback below.
        pass
    return InternalProvider.get_provider()


def dispose_current_container():
    """
    Dispose of the current request's scoped container.
    In Flask/Quart, call this in a teardown handler.
    """
    try:
        from flask import has_request_context, g
        if has_request_context() and hasattr(g, 'di_container'):
            g.di_container.dispose()
            del g.di_container
    except ImportError:
        pass


class InternalProvider:
    service_provider = None

    @classmethod
    def bind(cls, service_provider):
        """
        Binds a service provider to the internal provider.
        """
        if cls.service_provider is None:
            cls.service_provider = service_provider
        logger.info('Bound service provider to internal provider')

    @classmethod
    def resolve(cls, _type: type):
        """
        Resolves a service for a given type using the current container.
        (For scoped dependencies, use the scope if available.)
        """
        return get_current_container().resolve(_type)

    @classmethod
    def get_provider(cls):
        """
        Returns the root service provider.
        """
        return cls.service_provider


class ProviderBase:
    """
    Base class for providers.
    """
    service_provider = None
    _lock = threading.RLock()  # Add a reentrant lock for thread safety

    @classmethod
    def initialize_provider(cls):
        """
        Initializes the service provider.
        """
        _ = cls.get_service_provider()

    @classmethod
    def configure_container(cls):
        """
        Configures the container.
        To be implemented by subclasses.
        """
        pass

    @classmethod
    def get_service_provider(cls):
        """
        Returns the service provider, building it if necessary.
        Thread-safe: ensures only one thread can initialize the provider.
        """
        if cls.service_provider is None:
            with cls._lock:
                if cls.service_provider is None:
                    container = cls.configure_container()
                    # Build the service provider (which will prebuild singleton/factory dependencies)
                    service_provider = ServiceProvider(container)
                    service_provider.build()
                    cls.service_provider = service_provider
                    # Bind the root provider to the internal provider.
                    InternalProvider.bind(service_provider=service_provider)
        return cls.service_provider


def get_function_args(func):
    """
    Returns the argument names for a given function.
    """
    return list(inspect.signature(func).parameters)


def inject_container_async(func):
    """
    Asynchronously injects the container into a function if it requires it.
    The injected container will be the current (scoped if available) container.
    """
    async def wrap(*args, **kwargs):
        func_args = get_function_args(func)
        if 'container' in func_args:
            return await func(*args, **kwargs, container=get_current_container())
        return await func(*args, **kwargs)
    return wrap


def inject_container(func):
    """
    Injects the container into a function if it requires it.
    The injected container will be the current (scoped if available) container.
    """
    def wrap(*args, **kwargs):
        func_args = get_function_args(func)
        if 'container' in func_args:
            return func(*args, **kwargs, container=get_current_container())
        return func(*args, **kwargs)
    return wrap
