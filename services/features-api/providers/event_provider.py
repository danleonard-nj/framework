import asyncio
from datetime import datetime
from typing import Dict

from domain.rest import FeatureLastEvaluatedRequest
from services.event_service import EventService
from services.feature_service import FeatureService


class EventProvider:
    def __init__(
        self,
        event_service: EventService,
        feature_service: FeatureService
    ):
        self.__event_service = event_service
        self.__feature_service = feature_service

    async def dispatch_feature_evaluated_event(
        self,
        feature_id: str,
        evaluated_date: datetime
    ):
        await self.__event_service.dispatch_feature_evaluated_event(
            feature_id=feature_id,
            evaluated_date=evaluated_date)

    async def update_feature_last_evaluated_date(
        self,
        body: Dict
    ):
        update_request = FeatureLastEvaluatedRequest.from_body(
            data=body)

        return await self.__feature_service.update_feature_last_evaluated_date(
            feature_id=update_request.feature_id,
            last_evaluated=update_request.last_evaluated)
