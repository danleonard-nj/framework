import inspect
from typing import Any, Dict, List

from framework.logger.providers import get_logger

logger = get_logger(__name__)


class Activator:
    @staticmethod
    def create_instance(_type: type, container=None):
        if len(inspect.signature(_type).parameters) == 0:
            return _type()
        else:
            return _type(container)


class DependencyProxy:
    def __init__(self, dependency_type=None):
        self._type = dependency_type
        self._calls = []

    def __call__(self):
        pass

    def __getattr__(self):
        pass


class DependencyType:
    SINGLETON = 'singleton'
    TRANSIENT = 'transient'
    SCOPED = 'scoped'


class Dependency:
    def __init__(self, _type, reg_type, instance=None, factory=None):
        self._type = _type
        self.reg_type = reg_type
        self.instance = instance
        self.factory = factory

    def activate(self):
        pass


class ContainerBase:
    def resolve(self, _type):
        pass


class Container(ContainerBase):
    def __init__(self):
        self.__container: Dict[type, Dependency] = {}
        self.__deferred_instance_registrations: List[Dependency] = []
        self.__factories: List[Dependency] = []
        self.__built = False

    def build(self) -> 'Container':
        # New up instances of dependencies registered as singletons or
        # factory singletons
        for dependency in self.__deferred_instance_registrations:
            self.__construct_deferred_instance(dependency)

        # New up factory dependency instances, order matters here
        # because we want the container singletons available to
        # the factory methods
        self.__handle_factory_dependencies()

        # Replace placeholder 'proxy' dependencies with the constructed
        # instances where applicable.  This enables non-linear order of
        # registration
        #
        # i.e. dependency B resolves dependency A and dependency B is
        # registered first, the instance of dependency A thats resolved
        # by dependency B is a 'DependencyProxy' object, and a reference
        # to that object is held in the container and replaced with the
        # actual dependency when is becomes availabe, or throws if it is
        # never registered
        self.__handle_proxy_dependencies()

        self.__built = True
        return self

    def __handle_factory_dependencies(self):
        for dependency in self.__factories:
            dependency.instance = dependency.factory(self)
            self.__container[dependency._type] = dependency

    def __handle_proxy_dependencies(self):
        _instances = [
            x.instance
            for x in self.__container.values()
            if x.instance is not None
        ]

        # Replace any dependency proxies in registered dependencies with the
        # actual instance.  In order to avoid complexity
        for instance in _instances:
            for key, value in instance.__dict__.items():

                if isinstance(value, DependencyProxy):
                    _rep_instance: Dependency = self.__container.get(
                        value._type)

                    if _rep_instance is None:
                        raise Exception(
                            f'Dependency {str(value._type)} is not registered')

                    setattr(instance, key, _rep_instance.instance)

    def has_constructor_params(
        self,
        _type: type
    ) -> bool:
        '''
        Verify class has constructor parameters
        '''

        sig = inspect.signature(_type).parameters

        if any(sig or []):
            return any([s for s in sig.keys() if s != 'container'])

    def __validate_dependency_registration(
        self,
        dependency: Dependency
    ) -> None:
        '''
        Validate a registered dependency
        '''

        if dependency.instance is not None and dependency.reg_type == 'transient':
            raise Exception(
                'Instance cannot be provided when registration type is transient')

        if dependency.instance is not None and dependency.reg_type == 'scoped':
            raise Exception(
                'Instance cannot be provided when registration type is scoped')

        if dependency.instance is None and dependency.reg_type == 'singleton':
            raise Exception(
                'Instance cannot be null when registration type is singleton')

    def __register_dependency(
        self,
        dependency_type: type,
        reg_type: str,
        instance: Any = None
    ) -> None:
        '''
        Register a dependency and add it to the container
        '''

        dependency = Dependency(
            _type=dependency_type,
            reg_type=reg_type,
            instance=instance)

        self.__validate_dependency_registration(
            dependency=dependency)

        self.__container[dependency_type] = dependency

    def add_transient(self, dependency_type):
        self.__register_dependency(
            dependency_type=dependency_type,
            reg_type=DependencyType.TRANSIENT)

    def add_scoped(self, dependency_type):
        self.__register_dependency(
            dependency_type=dependency_type,
            reg_type=DependencyType.SCOPED)

    def add_singleton(self, _type, instance=None):
        if instance is None and self.has_constructor_params(_type):
            raise Exception(
                f'Type must contain a parameterless constructor when passed implicitly')

        dependency = Dependency(
            reg_type=DependencyType.SINGLETON,
            _type=_type,
            instance=instance)

        # Add to registrations, these dependencies need prep before they're ready
        # to be hooked into the container (for singletons, an instance needs to
        # be created and stored)
        self.__deferred_instance_registrations.append(dependency)

    def add_factory_singleton(self, _type, factory):
        dependency = Dependency(
            reg_type=DependencyType.SINGLETON,
            _type=_type,
            factory=factory)

        # Add to registrations, these dependencies need prep before they're ready
        # to be hooked into the container (for singletons, an instance needs to
        # be created and stored)
        self.__factories.append(dependency)

    def __create_instance(self, _type):
        '''  Create an instance of a registered dependency with the container as an arg '''

        return Activator.create_instance(
            _type=_type,
            container=self)

    def __construct_deferred_instance(self, dependency: Dependency):
        ''' Construct instances of dependencies registered as singleton '''

        try:
            if dependency.reg_type in [DependencyType.TRANSIENT, DependencyType.SINGLETON]:
                self.__register_dependency(
                    dependency_type=dependency._type,
                    reg_type=DependencyType.SINGLETON,
                    instance=dependency.instance or self.__create_instance(
                        dependency._type))

        except Exception as ex:
            raise Exception(
                f'Failed to create instance of type {str(dependency._type)}: {str(ex)}')

    def resolve(self, _type):
        '''
        Resolve a dependency from the container

        `_type`: the type to resolve
        '''

        # If the container is not built, and a registered singleton call the resolve
        # on the container in its constructor, we can't guarantee that dependency it
        # is requesting in the constructor exists yet.  Instead, we'll pass back a
        # dependency proxy object that will be replaced with the actual instance when
        # the container is built
        if not _type in self.__container:
            dependency_proxy_type = type(
                f'Proxy{_type.__class__.__name__}', (_type,), dict())

            dependency_proxy_type._type = _type
            return DependencyProxy(dependency_type=_type)

        registration: Dependency = self.__container.get(_type)

        if registration.reg_type == DependencyType.TRANSIENT:
            return self.__create_instance(_type)

        if registration.reg_type == DependencyType.SINGLETON:
            return registration.instance

        if registration.reg_type == DependencyType.SCOPED:
            # Handle resolving scoped dependencies in the constuction of transient
            # and singleton service, we'll pass a dependency proxy and replace with
            # an instance in the scope
            if not self.__built and not self.__scope:
                return DependencyProxy(dependency_type=registration._type)

            if not self.__scope:
                raise Exception(
                    f"Cannot resolve a scoped dependency when no active scope exists")

            return registration.instance

        raise Exception('Unsupported registration type')

    def __getitem__(self, key: type):
        if key in self.__container:
            return self.__container[key]
        raise Exception(f"No registration for type '{key.__name__}' exists")

    def create_scope(self):
        ''' Create scoped instances and open scope '''

        logger.info(f'Creating scope')
        for _type, dependency in self.__container.items():
            logger.info(f'Creating dependency: {_type.__name__}')
            if dependency.reg_type == DependencyType.SCOPED:
                if dependency.factory is not None:
                    # TODO: Scoped factories
                    pass

                else:
                    dependency.instance = Activator.create_instance(
                        _type=_type,
                        container=self)

        logger.info(f'Setting scope state to true')
        self.__scope = True

    def dispose_scope(self):
        ''' Destroy scoped instances and close scope '''

        logger.info(f'Disposing scope')
        for _type, dependency in self.__container.items():
            if dependency.reg_type == DependencyType.SCOPED:
                dependency.instance = None

        logger.info('Setting scope state to false')
        self.__scope = False
