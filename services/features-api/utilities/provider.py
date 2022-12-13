from data.feature_repository import FeatureRepository
from framework.abstractions.abstract_request import RequestContextProvider
from framework.clients.keyvault_client import AzureKeyVaultClient
from framework.configuration.configuration import Configuration
from framework.dependency_injection.container import Container
from framework.dependency_injection.provider import ProviderBase
from framework.middleware.authorization import AuthMiddleware
from quart import Quart, request
from services.feature_service import FeatureService


def configure_middleware(container):
    configuration = container.resolve(Configuration)
    keyvault_client = container.resolve(AzureKeyVaultClient)

    certificate_name = configuration.security.certificate_name
    if not certificate_name:
        raise ValueError('Certificate name cannot be null')
    public_key = keyvault_client.get_certificate_public_key(
        certificate_name=certificate_name)

    return AuthMiddleware(
        public_key=public_key)


class ContainerProvider(ProviderBase):
    @classmethod
    def configure_container(cls):
        container = Container()

        container.add_singleton(Configuration)
        container.add_singleton(AzureKeyVaultClient)

        container.add_factory_singleton(
            _type=AuthMiddleware,
            factory=configure_middleware)

        container.add_singleton(FeatureRepository)
        container.add_transient(FeatureService)

        return container.build()


def add_container_hook(app: Quart):
    RequestContextProvider.initialize_provider(
        app=app)

    def inject_container():
        if request.view_args != None:
            request.view_args['container'] = ContainerProvider.get_container()

    app.before_request_funcs.setdefault(
        None, []).append(
            inject_container)
