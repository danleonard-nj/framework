from framework.logger import get_logger
from motor.motor_asyncio import AsyncIOMotorClient

from constants.mongo import MongoConstants
from data.async_mongo_repository import MongoRepositoryAsync

logger = get_logger(__name__)


class FeatureRepository(MongoRepositoryAsync):
    def __init__(
        self,
        client: AsyncIOMotorClient
    ) -> None:

        super().__init__(
            client=client,
            collection=MongoConstants.FeatureCollection,
            database=MongoConstants.DatabaseName)

    async def feature_key_exists(
        self,
        feature_key: str
    ):
        exists = await self.get({
            'feature_key': feature_key
        })

        return exists is not None
