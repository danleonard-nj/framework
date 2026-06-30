import asyncio
import inspect
from collections import defaultdict
from functools import wraps
from threading import Lock, RLock
from typing import Any, Callable, Dict, List, Optional, Set

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

        self._singleton_instances: dict[type, Any] = {}
        # RLock is required for recursive synchronous dependency resolution:
        # singleton A's constructor may call resolve(B), which re-enters this
        # lock on the same thread. A plain Lock would deadlock.
        self._cache_lock = RLock()

        # Per-type asyncio.Lock objects for coroutine-safe lazy singleton
        # construction. A single global async lock would deadlock when singleton
        # A's async constructor awaits resolve_async(B) (A → B → lock already
        # held). Unrelated singleton types must also not serialise each other.
        self._async_singleton_locks: dict[type, asyncio.Lock] = {}
        # Tiny synchronous lock protecting only the lock-dictionary itself;
        # never held across construction or any await.
        self._async_lock_registry = Lock()

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
        dep_type = registration.dependency_type

        if registration.lifetime == Lifetime.Transient:
            if registration.factory:
                result = registration.factory(self)
                if inspect.isawaitable(result):
                    raise RuntimeError(
                        f"Factory for '{dep_type.__name__}' returned an awaitable. "
                        "Use resolve_async() to resolve async factories.")
                return result
            return registration.activate(self)

        elif registration.lifetime == Lifetime.Singleton:
            # Fast path: lock-free cache check
            instance = self._singleton_instances.get(dep_type)
            if instance is not None:
                return instance

            # Fall back to registration.instance (set during build())
            if registration.instance is not None:
                self._singleton_instances[dep_type] = registration.instance
                return registration.instance

            # Lazy singleton creation with double-checked locking.
            # RLock allows the same thread to re-enter while constructing
            # nested singletons (e.g. A's constructor resolves B).
            with self._cache_lock:
                instance = self._singleton_instances.get(dep_type)
                if instance is not None:
                    return instance
                if registration.factory:
                    result = registration.factory(self)
                    if inspect.isawaitable(result):
                        raise RuntimeError(
                            f"Factory for '{dep_type.__name__}' returned an awaitable. "
                            "Use resolve_async() to resolve async factories.")
                    instance = result
                else:
                    instance = registration.activate(self)
                registration.instance = instance
                self._singleton_instances[dep_type] = instance
                return instance

        elif registration.lifetime == Lifetime.Scoped:
            raise Exception('Scoped resolution requires a scope. Call provider.create_scope().')

        raise Exception(f"Unknown lifetime: {registration.lifetime}")

    def _get_async_singleton_lock(self, dep_type: type) -> asyncio.Lock:
        '''
        Returns (creating lazily if needed) the per-type asyncio.Lock used for
        coroutine-safe lazy singleton construction. Only the dictionary lookup
        is protected by a synchronous lock; it is never held across construction
        or an await.
        '''
        with self._async_lock_registry:
            lock = self._async_singleton_locks.get(dep_type)
            if lock is None:
                lock = asyncio.Lock()
                self._async_singleton_locks[dep_type] = lock
        return lock

    async def resolve_async(self, _type: type) -> Any:
        '''
        Resolves a service for a given type asynchronously.
        '''
        logger.debug(f"Resolving (async) service for type: {_type.__name__}")

        registration = self._get_registered_dependency(implementation_type=_type)
        dep_type = registration.dependency_type

        if registration.lifetime == Lifetime.Singleton:
            instance = self._singleton_instances.get(dep_type)
            if instance is not None:
                return instance

            if registration.instance is not None:
                self._singleton_instances[dep_type] = registration.instance
                return registration.instance

            # Per-type asyncio.Lock so that:
            # 1. Concurrent coroutines for the same type create exactly one instance.
            # 2. Nested resolution of a different type (A → B) uses B's own lock
            #    and is not serialised with A's construction.
            # 3. The lock is never held across construction or any await of an
            #    unrelated resource — only across this singleton's own construction.
            async_lock = self._get_async_singleton_lock(dep_type)
            async with async_lock:
                # Double-check after acquiring: another coroutine may have
                # already constructed the instance while we waited.
                instance = self._singleton_instances.get(dep_type)
                if instance is not None:
                    return instance
                if registration.factory:
                    inst = registration.factory(self)
                    if inspect.isawaitable(inst):
                        inst = await inst
                    instance = inst
                else:
                    instance = await registration.activate_async(self)
                registration.instance = instance
                self._singleton_instances[dep_type] = instance
                return instance

        elif registration.lifetime == Lifetime.Transient:
            if registration.factory:
                inst = registration.factory(self)
                return await inst if inspect.isawaitable(inst) else inst
            return await registration.activate_async(self)

        elif registration.lifetime == Lifetime.Scoped:
            raise Exception('Scoped resolution requires a scope. Call provider.create_scope().')

        raise Exception(f"Unknown lifetime: {registration.lifetime}")

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

    def _validate_and_order(self) -> List[DependencyRegistration]:
        '''
        Validates all singleton registrations and returns the topologically
        ordered build list of singletons + factories. Raises if any singleton
        depends on a transient or if a dependency cycle exists.
        '''
        # Verify all singletons don't have transient dependencies
        for registration in self.singleton_registrations:
            self._verify_singleton(registration)

        to_build = self.singleton_registrations + self.factory_registrations
        dependency_graph = self._create_dependency_graph(to_build)
        build_order = self._topological_sort(dependency_graph)

        if build_order is None:
            raise InvalidDependencyChainError()

        return build_order

    def build(self) -> 'ServiceProvider':
        '''
        Builds the service provider by validating all registrations and
        eagerly constructing factories and any singletons explicitly marked
        as eager. Other singletons are constructed lazily on first resolve().
        '''
        build_order = self._validate_and_order()

        # Build dependencies in topological order, but only those that should
        # be constructed eagerly. Lazy singletons are validated and ordered
        # here but constructed on first resolve() via the cache fast path.
        for registration in build_order:
            if not (registration.is_factory or registration.eager):
                continue

            if registration.is_factory:
                # For factories, pass the provider into the factory function
                inst = registration.factory(self)
                # Support coroutine factories
                if asyncio.iscoroutine(inst):
                    try:
                        loop = asyncio.get_running_loop()
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as ex:
                            inst = ex.submit(asyncio.run, inst).result()
                    except RuntimeError:
                        inst = asyncio.run(inst)
                registration.instance = inst
            else:
                # Capture the return value; do not rely solely on activate()
                # mutating registration.instance as a side-effect.
                registration.instance = registration.activate(self)

            with self._cache_lock:
                self._singleton_instances[registration.dependency_type] = registration.instance
            self._set_built_dependency(registration)

        return self

    async def build_async(self) -> 'ServiceProvider':
        '''
        Async variant of build(), awaiting any coroutine constructors or factories.
        '''
        build_order = self._validate_and_order()

        for registration in build_order:
            if not (registration.is_factory or registration.eager):
                continue

            if registration.is_factory:
                inst = registration.factory(self)
                if asyncio.iscoroutine(inst):
                    inst = await inst
                registration.instance = inst
            else:
                registration.instance = await registration.activate_async(self)

            with self._cache_lock:
                self._singleton_instances[registration.dependency_type] = registration.instance
            self._set_built_dependency(registration)

        return self

    def create_scope(self) -> 'ServiceScope':
        '''Begin a new scoped lifetime context.'''
        return ServiceScope(self)

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


class ServiceScope:
    '''
    Provides scoped resolution: Singleton → cascades to root provider, Transient → new each call,
    Scoped → one instance per scope.
    '''

    def __init__(self, provider: 'ServiceProvider'):
        self._provider = provider
        self._scoped_instances: dict[type, Any] = {}
        self._dependency_lookup = provider._dependency_lookup
        self._cache_lock = Lock()

    def __enter__(self) -> 'ServiceScope':
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.dispose()

    async def __aenter__(self) -> 'ServiceScope':
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        for inst in self._scoped_instances.values():
            if hasattr(inst, '__aexit__'):
                await inst.__aexit__(exc_type, exc_value, traceback)
        self.dispose()

    def resolve(self, _type: type) -> Any:
        provider = self._provider
        reg = provider._get_registered_dependency(_type)

        if reg.lifetime == Lifetime.Singleton:
            return provider.resolve(_type)

        insts = self._scoped_instances

        if reg.lifetime == Lifetime.Scoped:
            inst = insts.get(_type)
            if inst is not None:
                return inst

        if reg.factory:
            inst = reg.factory(self)
        elif hasattr(reg, '_resolver_fn') and reg._resolver_fn is not None:
            inst = reg._resolver_fn(self)
        else:
            inst = reg.activate(self)

        if reg.lifetime == Lifetime.Scoped:
            insts[_type] = inst

        return inst

    async def resolve_async(self, _type: type) -> Any:
        provider = self._provider
        reg = provider._get_registered_dependency(_type)

        if reg.lifetime == Lifetime.Singleton:
            return await provider.resolve_async(_type)

        insts = self._scoped_instances

        if reg.lifetime == Lifetime.Scoped:
            inst = insts.get(_type)
            if inst is not None:
                return inst

        if reg.factory:
            inst = reg.factory(self)
            if asyncio.iscoroutine(inst):
                inst = await inst
        else:
            inst = await reg.activate_async(self)

        if reg.lifetime == Lifetime.Scoped:
            insts[_type] = inst

        return inst

    def dispose(self) -> None:
        '''
        Clear scoped instances. Calls dispose() on any instance that exposes it.
        '''
        for instance in self._scoped_instances.values():
            if hasattr(instance, 'dispose') and callable(instance.dispose):
                try:
                    instance.dispose()
                except Exception as e:
                    logger.warning(f"Error disposing scoped instance: {e}")

        self._scoped_instances.clear()


class DependencyInjector:
    '''
    Decorator and middleware helper for auto-injecting registered dependencies
    into function parameters based on type annotations.
    '''

    def __init__(self, provider: ServiceProvider, strict: bool = False):
        self._provider = provider
        self._strict = strict

    def create_scope(self) -> ServiceScope:
        '''Expose ability to create a manual scope.'''
        return self._provider.create_scope()

    def inject(self, fn: Callable) -> Callable:
        '''
        Decorator for sync or async functions. Fills annotated params from the
        registered provider (or active scope if attached via middleware).

        In strict mode all annotated params must be registered.
        In non-strict mode only registered params are injected; others are left to the caller.
        '''
        from framework.di.service_collection import get_signature
        sig = get_signature(fn)
        is_async = asyncio.iscoroutinefunction(fn)

        new_params = []
        injectable_params = {}

        for name, param in sig.parameters.items():
            if param.annotation != inspect.Parameter.empty:
                if self._strict:
                    if param.annotation not in self._provider._dependency_lookup:
                        raise ValueError(
                            f"Failed to resolve dependency '{param.annotation.__name__}' "
                            f"for parameter '{name}': dependency is not registered")
                    injectable_params[name] = param.annotation
                else:
                    if param.annotation in self._provider._dependency_lookup:
                        injectable_params[name] = param.annotation
                    else:
                        new_params.append(param)
            else:
                new_params.append(param)

        new_sig = sig.replace(parameters=new_params)

        if is_async:
            @wraps(fn)
            async def async_wrapper(*args, **kwargs):
                if hasattr(async_wrapper, '_scope') and async_wrapper._scope is not None:
                    resolve_method = async_wrapper._scope.resolve_async
                else:
                    resolve_method = self._provider.resolve_async

                for name, param_type in injectable_params.items():
                    if name not in kwargs:
                        try:
                            kwargs[name] = await resolve_method(param_type)
                        except Exception as e:
                            if self._strict:
                                raise ValueError(
                                    f"Failed to resolve dependency '{param_type.__name__}' "
                                    f"for '{name}': {e}")
                            logger.debug(f"Skipping DI for '{name}': {e}")
                return await fn(*args, **kwargs)

            async_wrapper.__signature__ = new_sig
            async_wrapper._scope = None
            return async_wrapper
        else:
            @wraps(fn)
            def sync_wrapper(*args, **kwargs):
                if hasattr(sync_wrapper, '_scope') and sync_wrapper._scope is not None:
                    resolver = sync_wrapper._scope
                else:
                    resolver = self._provider

                for name, param_type in injectable_params.items():
                    if name not in kwargs:
                        try:
                            kwargs[name] = resolver.resolve(param_type)
                        except Exception as e:
                            if self._strict:
                                raise ValueError(
                                    f"Failed to resolve dependency '{param_type.__name__}' "
                                    f"for '{name}': {e}")
                            logger.debug(f"Skipping DI for '{name}': {e}")
                return fn(*args, **kwargs)

            sync_wrapper.__signature__ = new_sig
            sync_wrapper._scope = None
            return sync_wrapper

    def setup_fastapi(self, app) -> None:
        '''
        Install FastAPI middleware to create a new scope per request and wire
        decorated endpoints.
        '''
        from fastapi import Request

        @app.middleware('http')
        async def di_middleware(request: Request, call_next):
            with self.create_scope() as scope:
                request.state.scope = scope
                for route in app.routes:
                    if hasattr(route, 'endpoint') and hasattr(route.endpoint, '_scope'):
                        route.endpoint._scope = scope
                return await call_next(request)

    def setup_flask(self, app) -> None:
        '''
        Install Flask hooks to manage a scope per request via flask.g.
        '''
        from flask import g

        @app.before_request
        def before_request():
            g.scope = self.create_scope()

        @app.teardown_request
        def teardown_request(exception=None):
            if hasattr(g, 'scope'):
                g.scope.dispose()

        for rule in app.url_map.iter_rules():
            endpoint = app.view_functions[rule.endpoint]
            if hasattr(endpoint, '_scope'):
                @wraps(endpoint)
                def wrapped_view(*args, **kwargs):
                    endpoint._scope = g.scope
                    return endpoint(*args, **kwargs)
                app.view_functions[rule.endpoint] = wrapped_view
