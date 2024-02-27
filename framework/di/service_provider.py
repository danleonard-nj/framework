import re
from time import time
from typing import Any, List, Optional

from framework.di.dependencies import DependencyRegistration, Lifetime
from framework.di.exceptions import (InvalidDependencyChainError,
                                     RegistrationNotFoundError,
                                     RegistrationNotFoundForInstantiationError,
                                     TransientDependencyInjectionError)
from framework.di.service_collection import ServiceCollection
from framework.logger import get_logger

logger = get_logger(__name__)


class ServiceProvider:
    '''
    A class that provides services (dependencies) as per their registrations.
    '''

    @property
    def built_types(self) -> list[type]:
        '''
        Returns a list of types that have been built.
        '''
        return self._built_types

    @property
    def built_type_lookup(self) -> dict[type, DependencyRegistration]:
        '''
        Returns a dictionary mapping built types to their corresponding DependencyRegistration instances.
        '''
        return self._built_type_lookup

    @property
    def built_dependencies(self) -> list[DependencyRegistration]:
        '''
        Returns a list of DependencyRegistration instances that have been built.
        '''
        return self._built_dependencies

    @property
    def singleton_registrations(self) -> list[DependencyRegistration]:
        '''
        Returns a list of singleton DependencyRegistration instances.
        '''
        return self._singletons

    @property
    def factory_registrations(self) -> list[DependencyRegistration]:
        '''
        Returns a list of factory DependencyRegistration instances.
        '''
        return self._factories

    @property
    def transient_registrations(self) -> list[DependencyRegistration]:
        '''
        Returns a list of transient DependencyRegistration instances.
        '''
        return self._transients

    @property
    def transient_types(self) -> list[type]:
        '''
        Returns a list of transient types.
        '''
        return self._transient_types

    @property
    def to_instantiate(self) -> int:
        '''
        Returns the total number of dependencies to instantiate before the provider is considered built.
        '''
        return len(self.singleton_registrations) + len(self.factory_registrations)

    def __init__(self, service_collection: ServiceCollection):
        '''
        Initializes a ServiceProvider instance with a given ServiceCollection.
        '''
        container = service_collection.get_container()

        self._dependency_lookup = container
        self._dependencies = list(container.values())

        self._built_dependencies = []
        self._built_types = []
        self._built_type_lookup = dict()

        self._initialize_provider()

    def _initialize_provider(
        self
    ) -> None:
        '''
        Initializes the provider by categorizing dependencies into transients, factories, and singletons.
        '''
        self._transients = [x for x in self._dependencies
                            if x.lifetime == Lifetime.Transient]

        self._transient_types = [x.implementation_type
                                 for x in self._transients]

        self._factories = [x for x in self._dependencies
                           if x.lifetime == Lifetime.Singleton
                           and x.is_factory]

        self._singletons = [x for x in self._dependencies
                            if x.lifetime == Lifetime.Singleton
                            and not x.is_factory]

    def _set_built_dependency(
        self,
        registration: DependencyRegistration
    ) -> None:
        '''
        Marks a DependencyRegistration instance as built and updates the built types and dependencies.
        '''
        self._built_type_lookup[registration.implementation_type] = registration
        self._built_types.append(registration.implementation_type)
        self._built_dependencies.append(registration)

    def resolve(
        self, _type: type
    ) -> Any:
        '''
        Resolves a service for a given type.
        '''
        logger.debug(f"Resolving service for type: {_type._name_}")

        registration = self._get_registered_dependency(
            implementation_type=_type)

        if registration.lifetime == Lifetime.Transient:
            instance = registration.activate(self._dependency_lookup)
            return instance

        elif registration.lifetime == Lifetime.Singleton:
            return registration.instance

    def _verify_singleton(
        self,
        registration: DependencyRegistration
    ) -> None:
        '''
        Verifies that no singleton constructor param dependencies are transients.
        '''
        for required_type in registration.required_types:
            required_type_registration = self._get_registered_dependency(
                implementation_type=required_type, requesting_type=registration)

            if required_type_registration.lifetime == Lifetime.Transient:
                raise TransientDependencyInjectionError(
                    required_type=required_type,
                    registration=registration)

    def _can_build_type(
        self,
        registration: DependencyRegistration
    ) -> bool:
        '''
        Checks if a type can be built.
        '''
        if registration.lifetime == Lifetime.Singleton:
            return self._can_build_singleton_type(registration=registration)

    def _can_build_singleton_type(
        self,
        registration: DependencyRegistration
    ) -> bool:
        '''
        Checks if a singleton type can be built.
        '''
        self._verify_singleton(registration=registration)

        for required_type in registration.required_types:
            if required_type not in self.built_types:
                return False

        return True

    def _get_registered_dependency(
        self,
        implementation_type: type,
        requesting_type: Optional[DependencyRegistration] = None
    ) -> DependencyRegistration:
        '''
        Returns the DependencyRegistration instance for a given implementation type.
        '''
        registration = self._dependency_lookup.get(implementation_type)

        if registration is not None:
            return registration

        if requesting_type is not None:
            raise RegistrationNotFoundForInstantiationError(
                implementation_type, requesting_type)
        else:
            raise RegistrationNotFoundError(implementation_type)

    def build(
        self
    ) -> 'ServiceProvider':
        '''
        Builds the service provider by creating instances of all dependencies registered as singleton or factories.
        '''
        while len(self.built_dependencies) < self.to_instantiate:
            cycle_start = len(self.built_dependencies)
            self._build_singletons()
            self._build_factories()
            cycle_end = len(self.built_dependencies)

            # If no new dependencies were built, there is a circular dependency
            # and the provider cannot be built
            if cycle_start == cycle_end:
                raise InvalidDependencyChainError()

        return self

    def _build_singletons(
        self
    ) -> None:
        '''
        Builds all unbuilt singleton registrations.
        '''
        unbuilt_singletons = [registration for registration
                              in self.singleton_registrations
                              if not registration.built]

        # If the registration is parameterless, activate it and set it as built
        # Otherwise, check if it can be built and set it as built if it can
        # If it cannot be built, it will be built in a future cycle
        # when its dependencies are built if the dependency chain is valid

        for registration in unbuilt_singletons:

            if registration.is_parameterless:
                registration.activate(self._dependency_lookup)
                self._set_built_dependency(registration=registration)

            elif self._can_build_type(registration=registration):
                registration.activate(self._dependency_lookup)
                self._set_built_dependency(registration=registration)

    def _build_factories(self):
        '''
        Builds all unbuilt factory registrations.
        '''

        unbuilt_factories = [registration for registration
                             in self.factory_registrations
                             if not registration.built]

        for registration in unbuilt_factories:
            factory_instance = registration.factory(self)
            registration.instance = factory_instance

            self._set_built_dependency(registration=registration)
