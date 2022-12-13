from data.feature_repository import FeatureRepository
from models.feature import (
    CreateFeatureRequest,
    Feature,
    FeatureType,
    SetFeatureRequest
)
from typing import List

from framework.logger.providers import get_logger

logger = get_logger(__name__)


class FeatureService:
    def __init__(self, container=None):
        self.repository: FeatureRepository = container.resolve(
            FeatureRepository)

    async def get_feature_by_id(self, feature_id: str) -> dict:
        feature = await self.repository.get({
            'feature_id': feature_id
        })

        if feature is None:
            raise Exception(f"No feature with the ID '{feature_id}' exists")

        model = Feature(data=feature)
        return model.to_dict()

    async def delete_feature_by_id(self, feature_id: str) -> dict:
        feature = await self.repository.delete({
            'feature_id': feature_id
        })

        if feature is None:
            raise Exception(f"No feature with the ID '{feature_id}' exists")

        return {
            'result': feature.deleted_count > 0
        }

    async def get_feature_by_name(self, feature_name: str) -> dict:
        feature = await self.repository.get({
            'feature_name': feature_name
        })

        if feature is None:
            raise Exception(
                f"No feature with the name '{feature_name}' exists")

        model = Feature(data=feature)
        return model.to_dict()

    async def get_feature_by_key(self, feature_key: str) -> dict:
        feature = await self.repository.get({
            'feature_key': feature_key
        })

        if feature is None:
            raise Exception(f"No feature with the key '{feature_key}' exists")

        model = Feature(data=feature)
        return model.to_dict()

    async def get_all(self) -> List[dict]:
        features = await self.repository.get_all()

        return [
            Feature(data=feature).to_dict()
            for feature in features]

    async def evaluate_feature(self, feature_key: str) -> dict:
        feature = await self.get_feature_by_key(
            feature_key=feature_key)

        model = Feature(data=feature)

        logger.info(f'{model.feature_key}: {model.type_name}: {model.value}')

        return {
            'value': model.value
        }

    async def set_feature(self, feature_key: str, request: SetFeatureRequest) -> dict:
        feature = await self.get_feature_by_key(
            feature_key=feature_key)

        model = Feature(data=feature)

        # Validate the value matches the type
        if not FeatureType.validate_type(
                _type=model.type_id,
                value=request.value):
            raise Exception(
                f"'{request.value}' is not a valid value for feature type '{model.type_name}'")

        # Update the feature value
        model.value = request.value
        result = await self.repository.replace(
            document=model.to_dict(),
            selector={'feature_key': model.feature_key})

        return {
            'result': result.modified_count > 0
        }

    async def insert_feature(self, request: CreateFeatureRequest) -> dict:
        ''' Insert a feature into Mongo '''
        model = request.to_feature().set_feature_id()

        # Validate the feature type
        if not FeatureType.is_valid(
                _int=model.type_id):
            raise Exception(f"'{model.type}' is not a valid feature type")

        # Feature already exists with given key
        if await self.repository.feature_exists(
                feature_key=model.feature_key):
            raise Exception(
                f"A feature with the key '{model.feature_key}' already exists")

        await self.repository.insert(
            document=model.to_dict())
        return model.to_dict()
