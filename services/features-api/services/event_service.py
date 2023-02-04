from datetime import datetime
from threading import Thread

from framework.configuration import Configuration
from framework.logger import get_logger

from clients.event_client import EventClient
from clients.identity_client import IdentityClient
from domain.auth import ClientScope
from domain.events import UpdateFeatureLastEvaluatedDateEvent
from domain.rest import FeatureLastEvaluatedRequest
from services.feature_service import FeatureService

logger = get_logger(__name__)


class EventService:
    def __init__(
        self,
        configuration: Configuration,
        event_client: EventClient,
        identity_client: IdentityClient
    ):
        self.__event_client = event_client
        self.__identity_client = identity_client

        self.__app_base_url = configuration.events.get(
            'application_base_url')

    async def dispatch_feature_evaluated_event(
        self,
        feature_id: str,
        evaluated_date: datetime
    ):
        logger.info(f'Dispatching feature evaluated date update')

        event_request = FeatureLastEvaluatedRequest(
            feature_id=feature_id,
            last_evaluated=evaluated_date)

        logger.info('Fetching event auth token')
        token = await self.__identity_client.get_token(
            client_name='feature-api',
            scope=ClientScope.FeatureApi)

        event = UpdateFeatureLastEvaluatedDateEvent(
            body=event_request.to_dict(),
            endpoint=f'{self.__app_base_url}/api/events/evaluate',
            token=token)

        message = event.to_service_bus_message()
        event = Thread(
            target=self.__event_client.send_message,
            args=(message,))

        event.start()
        logger.info('Event dispatched successfully')
