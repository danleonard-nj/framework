from framework.data.mongo_repository import MongoRepositoryAsync
from framework.logger.providers import get_logger

from constants.mongo import MongoConstants

logger = get_logger(__name__)


def update_command(definition):
    return {'$set': definition}


class FeatureRepository(MongoRepositoryAsync):
    def __init__(self, container=None):
        self.initialize(
            container=container,
            collection=MongoConstants.COLLECTION_NAME,
            database=MongoConstants.DATABASE_NAME)

    async def feature_exists(self, feature_key):
        exists = await self.get({
            'feature_key': feature_key
        })

        return exists is not None
