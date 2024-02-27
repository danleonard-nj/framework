from typing import Any, Callable, Dict, List


class Lifetime:
    Singleton = 'singleton'
    Transient = 'transient'


class ConstructorDependency:
    @property
    def type_name(
        self
    ) -> str:
        self.dependency_type.__name__

    def __init__(
        self,
        name: str,
        _type: type
    ):
        self.name = name
        self.dependency_type = _type

    def __repr__(
        self
    ) -> str:
        return self.dependency_type.__name__


class DependencyRegistration:
    @property
    def type_name(
        self
    ) -> str:
        return self._type_name

    @property
    def is_factory(
        self
    ) -> bool:
        return self.factory is not None

    @property
    def required_types(
        self
    ) -> bool:
        return self._required_types

    @property
    def built(
        self
    ) -> bool:
        return self.instance is not None

    @property
    def is_parameterless(
        self
    ) -> bool:
        return len(self.constructor_params) == 0

    def __init__(
        self,
        dependency_type: type,
        lifetime: str,
        implementation_type: type = None,
        instance: Any = None,
        factory: Callable = None,
        constructor_params: List[ConstructorDependency] = None
    ):
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
        self._required_types = [dependency.dependency_type for
                                dependency in self.constructor_params]

        self._type_name = self.implementation_type.__name__

    def get_activate_constructor_params(
        self,
        dependency_lookup: Dict[str, 'DependencyRegistration']
    ):
        constructor_params = dict()

        for param in self.constructor_params:
            param_dependency = dependency_lookup.get(param.dependency_type)

            if param_dependency is None:
                raise Exception(
                    f"Could not find dependency for '{param.dependency_type}' when activating '{self.type_name}' constructor params")

            constructor_params[param.name] = param_dependency.activate(
                dependency_lookup=dependency_lookup)

        return constructor_params

    def activate(
        self,
        dependency_lookup: Dict[type, 'DependencyRegistration']
    ) -> Any:
        if self.lifetime == Lifetime.Singleton and self.built:
            return self.instance

        if (self.lifetime == Lifetime.Singleton
                and len(self.constructor_params) == 0):

            self.instance = self.implementation_type()
            return self.instance

        constructor_params = self.get_activate_constructor_params(
            dependency_lookup=dependency_lookup)

        if self.lifetime == Lifetime.Singleton:
            self.instance = self.implementation_type(**constructor_params)
            return self.instance

        if self.lifetime == Lifetime.Transient:
            return self.implementation_type(**constructor_params)
