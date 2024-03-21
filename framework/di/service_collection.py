import inspect
from typing import Any, Callable

from framework.di.dependencies import (ConstructorDependency,
                                       DependencyRegistration)


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
        params = inspect.signature(_type).parameters

        # Create a list of ConstructorDependency objects
        # for each parameter in the constructor
        types = []
        for name, param in params.items():
            if param.annotation == inspect._empty:
                raise Exception(
                    f"Encountered parameter with no annotation in type {_type.__name__}: {name}")

            constructor_dependency = ConstructorDependency(
                name=name,
                _type=param.annotation)
            types.append(constructor_dependency)
        return types

    def add_singleton(
        self,
        dependency_type: type,
        implementation_type: type = None,
        instance: Any = None,
        factory: Callable = None
    ) -> None:
        '''
        Adds a singleton dependency to the service collection.

        `dependency_type`: The type of the dependency
        `implementation_type` (type, optional): The type that implements the dependency
        `instance`: An instance of the dependency
        `factory`: A factory function that creates the dependency
        '''

        self._register_dependency(
            implementation_type=implementation_type,
            dependency_type=dependency_type,
            lifetime='singleton',
            instance=instance,
            factory=factory)

    def add_transient(
        self,
        dependency_type: type,
        implementation_type: type = None
    ) -> None:
        '''
        Adds a transient dependency to the service collection.

        `dependency_type`: The type of the dependency
        `implementation_type` (type, optional): The type that implements the dependency
        '''

        self._register_dependency(
            implementation_type=implementation_type,
            dependency_type=dependency_type,
            lifetime='transient')

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

        # Add the dependency to the container
        self._container[dependency_type] = dependency

    def get_container(
        self
    ) -> dict[type, DependencyRegistration]:
        '''
        Get the raw container
        '''

        return self._container
