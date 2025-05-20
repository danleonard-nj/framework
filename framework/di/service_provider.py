from typing import Any, Optional, Dict, List, Set
from collections import defaultdict

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
    Uses topological sorting to resolve dependencies in the correct order.
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
        self._built_type_lookup = {}

        self._initialize_provider()

    def _initialize_provider(self) -> None:
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

    def _set_built_dependency(self, registration: DependencyRegistration) -> None:
        '''
        Marks a DependencyRegistration instance as built and updates the built types and dependencies.
        '''
        self._built_type_lookup[registration.implementation_type] = registration
        self._built_types.append(registration.implementation_type)
        self._built_dependencies.append(registration)

    def resolve(self, _type: type) -> Any:
        '''
        Resolves a service for a given type.
        '''
        logger.debug(f"Resolving service for type: {_type.__name__}")

        registration = self._get_registered_dependency(implementation_type=_type)

        # Activate the dependency if it's a transient
        # with the current dependency lookup
        if registration.lifetime == Lifetime.Transient:
            instance = registration.activate(self._dependency_lookup)
            return instance

        # If it's a singleton simply return the instance
        elif registration.lifetime == Lifetime.Singleton:
            return registration.instance

    def _verify_singleton(self, registration: DependencyRegistration) -> None:
        '''
        Verifies that no singleton constructor param dependencies are transients.
        '''
        # Don't allow transient dependencies for singletons (only a single instance
        # of the transient dependency would be injected during instantiation of the
        # singleton, which is not the intended behavior of a transient dependency)
        for required_type in registration.required_types:
            required_type_registration = self._get_registered_dependency(
                implementation_type=required_type,
                requesting_type=registration)

            # If the required type is a transient, raise an error
            if required_type_registration.lifetime == Lifetime.Transient:
                raise TransientDependencyInjectionError(
                    required_type=required_type,
                    registration=registration)

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

    def build(self) -> 'ServiceProvider':
        '''
        Builds the service provider by creating instances of all dependencies 
        registered as singleton or factories using topological sorting.
        '''
        # Verify all singletons don't have transient dependencies
        for registration in self.singleton_registrations:
            self._verify_singleton(registration)

        # Create dependency graph for all non-transient registrations
        to_build = self.singleton_registrations + self.factory_registrations
        dependency_graph = self._create_dependency_graph(to_build)

        # Perform topological sort
        build_order = self._topological_sort(dependency_graph)

        if build_order is None:
            raise InvalidDependencyChainError()

        # Build dependencies in topological order
        for registration in build_order:
            if registration.is_factory:
                # For factories, pass the provider into the factory function
                factory_instance = registration.factory(self)
                registration.instance = factory_instance
            else:
                # For regular singletons, activate them
                registration.activate(self._dependency_lookup)

            self._set_built_dependency(registration)

        return self

    def _create_dependency_graph(self, registrations: List[DependencyRegistration]) -> Dict:
        '''
        Creates a dependency graph from a list of registrations.
        '''
        # Initialize graph
        graph = {
            'nodes': registrations,
            'edges': defaultdict(list),
            'in_degree': defaultdict(int)
        }

        # Create a lookup for registrations by implementation type
        registration_lookup = {reg.implementation_type: reg for reg in registrations}

        # For each registration, add edges from its dependencies to itself
        for registration in registrations:
            for required_type in registration.required_types:
                # Skip if the required type is not in the registrations to build
                # (it might be already built or a transient)
                if required_type in registration_lookup:
                    dependency = registration_lookup[required_type]
                    graph['edges'][dependency].append(registration)
                    graph['in_degree'][registration] += 1

        return graph

    def _topological_sort(self, graph: Dict) -> List[DependencyRegistration]:
        '''
        Performs a topological sort on the dependency graph.
        Returns None if there's a cycle in the graph.
        '''
        result = []

        # Get nodes with no incoming edges (no dependencies)
        queue = [node for node in graph['nodes']
                 if node.is_parameterless or graph['in_degree'][node] == 0]

        # Keep track of visited nodes
        visited = set()

        while queue:
            current = queue.pop(0)
            result.append(current)
            visited.add(current)

            # For each node that depends on the current node
            for neighbor in graph['edges'][current]:
                # Reduce the in-degree of the neighbor
                graph['in_degree'][neighbor] -= 1

                # If the neighbor has no more dependencies, add it to the queue
                if graph['in_degree'][neighbor] == 0:
                    queue.append(neighbor)

        # If we haven't visited all nodes, there's a cycle
        if len(visited) != len(graph['nodes']):
            return None

        return result
