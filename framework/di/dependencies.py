from typing import Any, Callable


class Lifetime:
    Singleton = 'singleton'
    Transient = 'transient'


class ConstructorDependency:
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
        constructor_params: list[ConstructorDependency] = None
    ):
        '''
        Initializes a DependencyRegistration object.

        `dependency_type`: The type of the dependency.
        `lifetime`: The lifetime of the dependency.
        `implementation_type`: The implementation type of the dependency.
        `instance`: The instance of the dependency.
        `factory`: The factory method of the dependency.
        `constructor_params`: The constructor parameters of the dependency.
        '''

        self.dependency_type = dependency_type
        self.lifetime = lifetime
        self.implementation_type = implementation_type or dependency_type
        self.instance = instance
        self.factory = factory
        self.constructor_params = constructor_params

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
        dependency_lookup: dict[str, 'DependencyRegistration']
    ) -> dict[str, Any]:
        '''
        Gets the activated constructor parameters for the dependency.

        `dependency_lookup`: A dictionary of dependency registrations.
        '''

        constructor_params = dict()

        # Verify that all other dependencies required by the this dependency
        # are registered
        for param in self.constructor_params:
            param_dependency = dependency_lookup.get(param.dependency_type)

            # The dependeyc required by the constructor parameter could not
            # be found in the dependency lookup (not registered)
            if param_dependency is None:
                raise Exception(
                    f"Could not find dependency for '{param.dependency_type}' when activating '{self.type_name}' constructor params")

            # Get activated instances of the dependencies required
            # to instantiate this dependency (to be passed as kwargs
            # downstream)
            constructor_params[param.name] = param_dependency.activate(
                dependency_lookup=dependency_lookup)

        return constructor_params

    def activate(
        self,
        dependency_lookup: dict[type, 'DependencyRegistration']
    ) -> Any:
        '''
        Get an activted instance of the dependency using the provided
        dependency lookup.

        `dependency_lookup`: A dictionary of dependency registrations.
        '''

        # If it's a singleton and we've already built the instance then
        # return the instance
        if self.lifetime == Lifetime.Singleton and self.built:
            return self.instance

        # If it's a singleton and there are no constructor parameters
        # then we can just return the instance
        if self.lifetime == Lifetime.Singleton and len(self.constructor_params) == 0:
            self.instance = self.implementation_type()
            return self.instance

        constructor_params = self.get_activate_constructor_params(
            dependency_lookup=dependency_lookup)

        if self.lifetime == Lifetime.Singleton:
            self.instance = self.implementation_type(**constructor_params)
            return self.instance

        if self.lifetime == Lifetime.Transient:
            return self.implementation_type(**constructor_params)
