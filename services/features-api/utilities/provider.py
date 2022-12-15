from framework.auth.azure import AzureAd
from framework.auth.configuration import AzureAdConfiguration
from framework.configuration.configuration import Configuration
from framework.di.service_collection import ServiceCollection
from framework.di.static_provider import ProviderBase
from motor.motor_asyncio import AsyncIOMotorClient

from data.feature_repository import FeatureRepository
from providers.feature_provider import FeatureProvider
from services.feature_service import FeatureService


def configure_azure_ad(service_descriptors):
    configuration = service_descriptors.resolve(Configuration)

    # Hook the Azure AD auth config into the service
    # configuration
    ad_auth: AzureAdConfiguration = configuration.ad_auth
    azure_ad = AzureAd(
        tenant=ad_auth.tenant_id,
        audiences=ad_auth.audiences,
        issuer=ad_auth.issuer)

    azure_ad.add_authorization_policy(
        name='default',
        func=lambda t: True)

    return azure_ad


def configure_mongo_client(service_provider):
    configuration = service_provider.resolve(Configuration)

    connection_string = configuration.mongo.get('connection_string')
    client = AsyncIOMotorClient(connection_string)

    return client


class ContainerProvider(ProviderBase):
    @classmethod
    def configure_container(cls):
        service_descriptors = ServiceCollection()

        service_descriptors.add_singleton(Configuration)
        service_descriptors.add_singleton(
            dependency_type=AzureAd,
            factory=configure_azure_ad)

        service_descriptors.add_singleton(
            dependency_type=AsyncIOMotorClient,
            factory=configure_mongo_client)

        # Repositories
        service_descriptors.add_singleton(FeatureRepository)

        # Services
        service_descriptors.add_transient(FeatureService)

        # Providers
        service_descriptors.add_transient(FeatureProvider)

        return service_descriptors
