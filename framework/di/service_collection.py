import inspect
from functools import lru_cache
from typing import Any, Callable, Optional

from framework.di.dependencies import (ConstructorDependency,
                                       DependencyRegistration,
                                       Lifetime)


@lru_cache(maxsize=2048)
def get_signature(fn):
    return inspect.signature(fn)


class ServiceCollection:
    def __init__(
        self
    ):
        self._container = dict()

    def get_type_dependencies(
        self,
        _type: type
    ) -> list:
        '''
        Get the types required to instantiate a type (constructor dependencies)

        `_type` (type): The type for which to retrieve the constructor dependencies.
        '''

        # Get the parameters of the constructor of the type
        params = get_signature(_type).parameters

        # Create a list of ConstructorDependency objects
        # for each parameter in the constructor
        types = []
        for name, param in params.items():
            if param.annotation == inspect.Parameter.empty:
                raise Exception(
                    f"Encountered parameter with no annotation in type {_type.__name__}: {name}")

            constructor_dependency = ConstructorDependency(
                name=name,
                _type=param.annotation)
            types.append(constructor_dependency)
        return types

    def add(
        self,
        dependency_type: type,
        implementation_type: Optional[type] = None,
        **kwargs
    ) -> None:
        '''
        Shorthand to register a service (default: Transient).
        '''
        kwargs.setdefault('lifetime', Lifetime.Transient)
        self._register_dependency(
            dependency_type=dependency_type,
            implementation_type=implementation_type,
            **kwargs)

    def add_singleton(
        self,
        dependency_type: type,
        implementation_type: type = None,
        instance: Any = None,
        factory: Callable = None,
        eager: bool = False
    ) -> None:
        '''
        Adds a singleton dependency to the service collection.

        `dependency_type`: The type of the dependency
        `implementation_type` (type, optional): The type that implements the dependency
        `instance`: An instance of the dependency
        `factory`: A factory function that creates the dependency
        `eager`: If True, construct the singleton at build() time instead of
            lazily on first resolve().
        '''

        self._register_dependency(
            implementation_type=implementation_type,
            dependency_type=dependency_type,
            lifetime='singleton',
            instance=instance,
            factory=factory,
            eager=eager)

    def add_transient(
        self,
        dependency_type: type,
        implementation_type: type = None,
        factory: Callable = None
    ) -> None:
        '''
        Adds a transient dependency to the service collection.

        `dependency_type`: The type of the dependency
        `implementation_type` (type, optional): The type that implements the dependency
        `factory`: A factory function that creates the dependency
        '''

        self._register_dependency(
            implementation_type=implementation_type,
            dependency_type=dependency_type,
            lifetime='transient',
            factory=factory)

    def add_scoped(
        self,
        dependency_type: type,
        implementation_type: type = None,
        factory: Callable = None
    ) -> None:
        '''
        Adds a scoped dependency to the service collection.

        `dependency_type`: The type of the dependency
        `implementation_type` (type, optional): The type that implements the dependency
        `factory`: A factory function that creates the dependency
        '''

        self._register_dependency(
            implementation_type=implementation_type,
            dependency_type=dependency_type,
            lifetime='scoped',
            factory=factory)

    def register_many(
        self,
        types: list[type],
        lifetime: str = Lifetime.Transient
    ) -> None:
        '''
        Bulk-register multiple types with the same lifetime.
        '''
        for t in types:
            getattr(self, f'add_{lifetime.lower()}')(t)

    def _register_dependency(
        self,
        implementation_type: type,
        dependency_type: type,
        **kwargs
    ) -> None:
        '''
        Register a dependency in the service collection.

        `implementation_type`: The type of the implementation for the dependency.
        `dependency_type`: The type of the dependency.
        `**kwargs`: Additional keyword arguments for configuring the dependency.
        '''

        # If implementation_type is None, use the dependency type
        # as the implementation_type
        if implementation_type is None:
            implementation_type = dependency_type

        # factory = kwargs.get('factory')
        constructor_params = (
            self.get_type_dependencies(
                _type=implementation_type)
            if kwargs.get('factory') is None else []
        )

        # Create the dependency registration
        dependency = DependencyRegistration(
            implementation_type=implementation_type,
            dependency_type=dependency_type,
            constructor_params=constructor_params,
            **kwargs)

        # Attach a precompiled resolver for use by ServiceScope
        impl = implementation_type
        captured_params = constructor_params

        def resolver_fn(provider, *_):
            return impl(
                **{param.name: provider.resolve(param.dependency_type)
                   for param in captured_params})

        dependency._resolver_fn = resolver_fn

        # Add the dependency to the container
        self._container[dependency_type] = dependency

    def get_container(
        self
    ) -> dict[type, DependencyRegistration]:
        '''
        Get the raw container
        '''

        return self._container

    def build_provider(self, eager_all: bool = False) -> 'ServiceProvider':
        '''
        Finalize registrations and return a built ServiceProvider.

        `eager_all`: If True, mark every singleton registration as eager so
            that all singletons are constructed at build() time (pre-lazy
            behavior).
        '''
        from framework.di.service_provider import ServiceProvider
        if eager_all:
            for registration in self._container.values():
                if registration.lifetime == Lifetime.Singleton:
                    registration.eager = True
        provider = ServiceProvider(self)
        provider.build()
        return provider
