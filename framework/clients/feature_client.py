from typing import Any, Tuple

import httpx

from framework.configuration.configuration import Configuration
from framework.exceptions.nulls import ArgumentNullException
from framework.logger.providers import get_logger

logger = get_logger(__name__)

DEFAULT_HEADER_KEY = 'X-Api-Key'


class FeatureClientAsync:
    def __init__(
        self,
        configuration: Configuration
    ):
        self.__base_url = configuration.features.get('base_url')
        self.__api_key = configuration.features.get('api_key')

        self.__enabled = configuration.features.get(
            'is_enabled', True)
        self.__header_key = configuration.features.get(
            'header_key', DEFAULT_HEADER_KEY)

        self.__validate_config()

    def __validate_config(
        self
    ):
        ArgumentNullException.if_none_or_whitespace(
            self.__base_url, 'base_url')
        ArgumentNullException.if_none_or_whitespace(
            self.__api_key, 'api_key')
        ArgumentNullException.if_none_or_whitespace(
            self.__header_key, 'header_key')

    def __get_headers(
        self
    ) -> dict:
        return {
            self.__header_key: self.__api_key
        }

    def get_disabled_feature_response(
        self,
        feature_key: str
    ) -> Tuple[dict, int]:
        '''
        Get a generic response value indicating
        a disabled featre

        `feature_key`: feature flag key
        '''

        return {
            'message': f"Feature '{feature_key}' is not enabled"
        }, 200

    async def is_enabled(
        self,
        feature_key: str
    ) -> Any:
        '''
        Get the state of a given feature flag

        `feature_key`: feature flag key
        '''

        logger.info(f'Evaluating feature flag: {feature_key}')

        if not self.__enabled:
            logger.info(f'Feature evaluation is disabled')
            return True

        endpoint = f'{self.__base_url}/api/feature/evaluate/{feature_key}'
        headers = self.__get_headers()

        logger.info(f'Endpoint: {endpoint}')
        logger.info(f'Headers: {headers}')

        try:
            async with httpx.AsyncClient(timeout=None) as client:
                response = await client.get(
                    url=endpoint,
                    headers=headers)

            content = response.json()
            return content.get('value')
        except Exception as ex:
            logger.info(
                f'Failed to fetch feature flag: {feature_key}: {str(ex)}')
            return False
