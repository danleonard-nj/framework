import inspect
from typing import Any, Callable, Dict

from framework.di.dependencies import (ConstructorDependency,
                                       DependencyRegistration)


class ServiceCollection:
    def __init__(self):
        self._container = dict()

    def get_type_dependencies(
        self,
        _type: type
    ) -> list:
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
        self._register_dependency(
            implementation_type=implementation_type,
            dependency_type=dependency_type,
            lifetime='transient')

    def _register_dependency(
            self,
            implementation_type,
            dependency_type,
            **kwargs
    ) -> None:
        # If implementation_type is None, use the dependency type
        # as the implementation_type
        if implementation_type is None:
            implementation_type = dependency_type

        factory = kwargs.get('factory')

        if factory is None:
            constructor_params = self.get_type_dependencies(
                _type=implementation_type)
        else:
            constructor_params = []

        dependency = DependencyRegistration(
            implementation_type=implementation_type,
            dependency_type=dependency_type,
            constructor_params=constructor_params,
            **kwargs)

        self._container[dependency_type] = dependency

    def get_container(
        self
    ) -> Dict[type, DependencyRegistration]:
        return self._container
