import asyncio
from typing import Any, Callable, Optional


class Lifetime:
    Singleton = 'singleton'
    Transient = 'transient'
    Scoped = 'scoped'


class ConstructorDependency:
    __slots__ = ('name', 'dependency_type')

    @property
    def type_name(self) -> str:
        '''
        The name of the dependency type.
        '''

        return self.dependency_type.__name__

    def __init__(
        self,
        name: str,
        _type: type
    ):
        '''
        Initializes a ConstructorDependency object.

        `name` (str): The name of the dependency.
        `_type` (type): The type of the dependency.
        '''

        self.name = name
        self.dependency_type = _type

    def __repr__(
        self
    ) -> str:
        '''
        A string representation of the ConstructorDependency object.
        '''

        return self.dependency_type.__name__


class DependencyRegistration:
    __slots__ = (
        'dependency_type', 'lifetime', 'implementation_type', 'instance',
        'factory', 'eager', 'constructor_params', '_type_name', '_required_types', '_resolver_fn'
    )

    @property
    def type_name(self) -> str:
        '''
        The name of the dependency type.
        '''

        return self._type_name

    @property
    def is_factory(self) -> bool:
        '''
        Indicates whether the dependency has a factory method.
        '''

        return self.factory is not None

    @property
    def required_types(self) -> bool:
        '''
        The list of required dependency types.
        '''

        return self._required_types

    @property
    def built(self) -> bool:
        '''
        Indicates whether the dependency has been built.
        '''

        return self.instance is not None

    @property
    def is_parameterless(self) -> bool:
        '''
        Indicates whether the dependency has a parameterless constructor.
        '''

        return len(self.constructor_params) == 0

    def __init__(
        self,
        dependency_type: type,
        lifetime: str,
        implementation_type: type = None,
        instance: Any = None,
        factory: Callable = None,
        eager: bool = False,
        constructor_params: list[ConstructorDependency] = None
    ):
        '''
        Initializes a DependencyRegistration object.

        `dependency_type`: The type of the dependency.
        `lifetime`: The lifetime of the dependency.
        `implementation_type`: The implementation type of the dependency.
        `instance`: The instance of the dependency.
        `factory`: The factory method of the dependency.
        `eager`: Whether a singleton should be constructed at build() time
            instead of lazily on first resolve().
        `constructor_params`: The constructor parameters of the dependency.
        '''

        self.dependency_type = dependency_type
        self.lifetime = lifetime
        self.implementation_type = implementation_type or dependency_type
        self.instance = instance
        self.factory = factory
        self.eager = eager
        self.constructor_params = constructor_params
        self._resolver_fn = None

        self.configure_dependency()

    def configure_dependency(
        self
    ) -> None:
        '''
        Configures the dependency by setting the required types and type name.
        '''

        self._required_types = [
            dependency.dependency_type for dependency in self.constructor_params]
        self._type_name = self.implementation_type.__name__

    def get_activate_constructor_params(
        self,
        provider
    ) -> dict[str, Any]:
        '''
        Gets the activated constructor parameters for the dependency.

        `provider`: A ServiceProvider or ServiceScope used to resolve dependencies.
        '''

        constructor_params = dict()

        for param in self.constructor_params:
            constructor_params[param.name] = provider.resolve(param.dependency_type)

        return constructor_params

    def activate(
        self,
        provider=None
    ) -> Any:
        '''
        Get an activated instance of the dependency.

        `provider`: A ServiceProvider or ServiceScope used to resolve constructor dependencies.
        '''

        # If it's a singleton and we've already built the instance then return it
        if self.lifetime == Lifetime.Singleton and self.built:
            return self.instance

        if not self.constructor_params:
            instance = self.implementation_type()
        else:
            constructor_params = self.get_activate_constructor_params(provider)
            instance = self.implementation_type(**constructor_params)

        if self.lifetime == Lifetime.Singleton:
            self.instance = instance

        return instance

    async def activate_async(
        self,
        provider=None
    ) -> Any:
        '''
        Async variant of activate, supporting coroutine constructors.

        `provider`: A ServiceProvider or ServiceScope used to resolve constructor dependencies.
        '''

        if self.lifetime == Lifetime.Singleton and self.built:
            return self.instance

        if not self.constructor_params:
            instance = self.implementation_type()
        else:
            kwargs = {}
            for param in self.constructor_params:
                kwargs[param.name] = await provider.resolve_async(param.dependency_type)
            instance = self.implementation_type(**kwargs)

        if self.lifetime == Lifetime.Singleton:
            self.instance = instance

        return instance
