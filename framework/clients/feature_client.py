from typing import Any, Dict

from httpx import AsyncClient
from werkzeug import Response

from framework.configuration.configuration import Configuration
from framework.exceptions.nulls import ArgumentNullException
from framework.logger.providers import get_logger

logger = get_logger(__name__)

DEFAULT_HEADER_KEY = 'X-Api-Key'


class FeatureClientAsync:
    def __init__(
        self,
        configuration: Configuration,
        http_client: AsyncClient
    ):
        ArgumentNullException.if_none(configuration, 'configuration')
        ArgumentNullException.if_none(http_client, 'http_client')

        self.__base_url = configuration.features.get(
            'base_url')
        self.__api_key = configuration.features.get(
            'api_key')

        self.__feature_client_enabled = configuration.features.get(
            'is_enabled', True)
        self.__header_key = configuration.features.get(
            'header_key', DEFAULT_HEADER_KEY)

        self.__http_client = http_client
        self.__validate_config()

    def __validate_config(
        self
    ) -> None:
        ArgumentNullException.if_none_or_whitespace(
            self.__base_url, 'base_url')
        ArgumentNullException.if_none_or_whitespace(
            self.__api_key, 'api_key')
        ArgumentNullException.if_none_or_whitespace(
            self.__header_key, 'header_key')

    def __get_headers(
        self
    ) -> Dict:
        return {
            self.__header_key: self.__api_key
        }

    def get_disabled_feature_response(
        self,
        feature_key: str
    ) -> Response:
        '''
        Get a generic response value indicating
        a disabled featre
        '''

        body = dict(
            message=f"Feature '{feature_key}' is not enabled")

        return Response(
            response=body,
            status=409)

    async def is_enabled(
        self,
        feature_key: str
    ) -> Any:
        '''
        Get the state of a given feature flag
        '''

        logger.debug(f'Evaluating feature flag: {feature_key}')

        if not self.__feature_client_enabled:
            logger.debug(f'Feature evaluation is disabled')
            return True

        # Endpoint to feature key value to fetch
        endpoint = f'{self.__base_url}/api/feature/evaluate/{feature_key}'
        logger.debug(f'Feature endpoint: {endpoint}')

        # Get request headers w/ auth
        headers = self.__get_headers()
        logger.debug(f'Headers: {headers}')

        try:
            response = await self.__http_client.get(
                url=endpoint,
                headers=headers)

            content = response.json()
            return content.get('value')

        except Exception as ex:
            logger.exception(
                f'Failed to fetch feature flag: {feature_key}: {str(ex)}')
            return False
