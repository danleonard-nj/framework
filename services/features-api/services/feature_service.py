from datetime import datetime
import json
from typing import Dict, List

from framework.logger.providers import get_logger

from data.feature_repository import FeatureRepository
from domain.exceptions import (ArgumentNullException, FeatureExistsException, FeatureKeyConflictException,
                               FeatureNotFoundException, InvalidFeatureTypeException)
from domain.feature import Feature, FeatureType, get_cardinality_key
from domain.rest import (CreateFeatureRequest, DeleteResponse,
                         EvaluateFeatureResponse, UpdateFeatureRequest)
from framework.crypto.hashing import sha256

logger = get_logger(__name__)


class FeatureService:
    def __init__(
        self,
        repository: FeatureRepository
    ):
        self.__repository = repository

    async def get_feature_by_id(
        self,
        feature_id: str
    ) -> Feature:

        entity = await self.__repository.get({
            'feature_id': feature_id
        })

        if entity is None:
            raise FeatureNotFoundException(
                value_type='ID',
                value=feature_id)

        feature = Feature.from_entity(
            data=entity)

        return feature

    async def delete_feature_by_id(
        self,
        feature_id: str
    ) -> DeleteResponse:
        '''
        Delete a featureby the ID feathe
        '''
        delete_result = await self.__repository.delete({
            'feature_id': feature_id
        })

        if delete_result is None:
            raise FeatureNotFoundException(
                value_type='ID',
                value=feature_id)

        return {
            'result': delete_result.deleted_count > 0
        }

    async def get_feature_by_name(
        self,
        feature_name: str
    ) -> Feature:

        logger.info(f'Get feature by name: {feature_name}')
        entity = await self.__repository.get({
            'feature_name': feature_name
        })

        if entity is None:
            raise FeatureNotFoundException(
                value_type='name',
                value=feature_name)

        feature = Feature.from_entity(
            data=entity)

        return feature

    async def get_feature_by_key(
        self,
        feature_key: str
    ) -> Feature:
        '''
        Get a feature by feature key
        '''

        logger.info(f'Get feature by key: {feature_key}')
        entity = await self.__repository.get({
            'feature_key': feature_key
        })

        if entity is None:
            raise FeatureNotFoundException(
                value_type='key',
                value=feature_key)

        feature = Feature.from_entity(
            data=entity)

        return feature

    async def get_all(
        self
    ) -> List[dict]:
        '''
        Get all features
        '''

        entities = await self.__repository.get_all()
        logger.info(f'{len(entities)} features fetched')

        features = [Feature.from_entity(data=entity)
                    for entity in entities]

        return features

    async def evaluate_feature(
        self,
        feature_key: str
    ) -> EvaluateFeatureResponse:
        '''
        Evaluate a feature
        '''

        ArgumentNullException.if_none_or_whitespace(
            feature_key, 'feature_key')

        entity = await self.__repository.get({
            'feature_key': feature_key
        })

        if entity is None:
            raise FeatureNotFoundException(
                value_type='key',
                value=feature_key)

        feature = Feature.from_entity(
            data=entity)

        return EvaluateFeatureResponse(
            feature=feature)

    async def update_feature(
        self,
        update: UpdateFeatureRequest
    ) -> Feature:
        '''
        Update a feature
        '''

        # Validate update request values
        ArgumentNullException.if_none(
            update, 'update_request')

        ArgumentNullException.if_none_or_whitespace(
            'feature_id', update.feature_id)

        ArgumentNullException.if_none_or_whitespace(
            'feature_type', update.feature_type)

        ArgumentNullException.if_none_or_whitespace(
            'name', update.name)

        ArgumentNullException.if_none_or_whitespace(
            'value', update.value)

        entity = await self.__repository.get({
            'feature_id': update.feature_id
        })

        if entity is None:
            raise FeatureNotFoundException(
                value_type='ID',
                value=update.feature_id)

        feature = Feature.from_entity(
            data=entity)

        logger.info(f'Feature cardinality key: {feature.cardinality_key}')
        logger.info(f'Update cardinality key: {update.cardinality_key}')

        # If no values have changed we can short out no update required
        if feature.cardinality_key == update.cardinality_key:
            logger.info(f'Cardinality match: {feature.cardinality_key}')
            return feature

        # Cardinality mismatch so update is required
        logger.info(f'Cardinality key mismatch update required')
        feature.modified_date = datetime.utcnow()

        # If the feature key was updated verify it doesn't conflict
        # with an existing feature key
        if feature.feature_key != update.feature_key:
            logger.info(f'Feature key update: {update.feature_key}')

            key_conflict = await self.__repository.feature_key_exists(
                feature_key=update.feature_key)
            logger.info(f'Feature key update conflict: {key_conflict}')

            if key_conflict:
                raise FeatureKeyConflictException(
                    feature_key=update.feature_key)

            # Update the feature key
            feature.feature_key = update.feature_key

        # Verify the feature type
        if feature.feature_type != update.feature_type:
            logger.info(f'Feature type update: {update.feature_type}')

            if update.feature_type not in FeatureType.types():
                raise InvalidFeatureTypeException(
                    feature_type=update.feature_type)

            # Update the feature type
            feature.feature_type = update.feature_type

        # Update feature values
        feature.name = update.name
        feature.description = update.description
        feature.value = update.value

        logger.info(f'Updated feature: {feature.to_dict()}')
        update_result = await self.__repository.replace(
            document=feature.to_dict(),
            selector=feature.get_selector())

        logger.info(f'Update result: {update_result.modified_count}')

        return feature

    async def create_feature(
        self,
        create_request: CreateFeatureRequest
    ) -> Feature:
        '''
        Create a feature
        '''

        # Feature already exists with given key
        if await self.__repository.feature_key_exists(
                feature_key=create_request.feature_key):

            raise FeatureExistsException(
                feature_key=create_request.feature_key)

        feature = Feature.from_create_feature_request(
            create_request=create_request)

        if not feature.is_valid_feature_type():
            raise InvalidFeatureTypeException(
                feature_type=feature.feature_type)

        logger.info(f"Inserting created feature: '{feature.feature_id}'")
        await self.__repository.insert(
            document=feature.to_dict())

        return feature
