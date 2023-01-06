import asyncio
from datetime import datetime
from typing import Dict

from domain.rest import CreateFeatureRequest, UpdateFeatureRequest
from providers.event_provider import EventProvider
from services.feature_service import FeatureService


class FeatureProvider:
    def __init__(
        self,
        feature_service: FeatureService,
        event_provider: EventProvider
    ):
        self.__feature_service = feature_service
        self.__event_provider = event_provider

    async def get_feature_by_id(
        self,
        feature_id: str
    ):
        feature = await self.__feature_service.get_feature_by_id(
            feature_id=feature_id)

        return feature.to_dict()

    async def delete_feature_by_id(
        self,
        feature_id: str
    ):
        return await self.__feature_service.delete_feature_by_id(
            feature_id=feature_id)

    async def get_feature_by_key(
        self,
        feature_key: str
    ) -> Dict:

        feature = await self.__feature_service.get_feature_by_key(
            feature_key=feature_key)

        return feature.to_dict()

    async def get_feature_by_name(
        self,
        feature_name: str
    ) -> Dict:

        feature = await self.__feature_service.get_feature_by_name(
            feature_name=feature_name)

        return feature.to_dict()

    async def create_feature(
        self,
        body: Dict
    ) -> Dict:
        create_feature = CreateFeatureRequest(
            data=body)

        feature = await self.__feature_service.create_feature(
            create_request=create_feature)

        return feature.to_dict()

    async def get_all(
        self
    ):
        return await self.__feature_service.get_all()

    async def evaluate_feature(
        self,
        feature_key: str
    ):
        result = await self.__feature_service.evaluate_feature(
            feature_key=feature_key)

        asyncio.create_task(self.__event_provider.dispatch_feature_evaluated_event(
            feature_id=result.feature_id,
            evaluated_date=datetime.now()))

        return result.to_dict()

    async def evaluate_feature_update(
        self,
        feature_key: str,
        body: Dict
    ):
        update_request = UpdateFeatureRequest(
            data=body)

        result = await self.__feature_service.evaluate_feature_update(
            feature_key=feature_key,
            value=update_request.value)

        return result.to_dict()

    async def update_feature(
        self,
        body: Dict
    ):
        feature_request = UpdateFeatureRequest(
            data=body)

        feature = await self.__feature_service.update_feature(
            update=feature_request)

        return feature.to_dict()
