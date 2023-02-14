from datetime import datetime
from typing import Any, List

from framework.logger.providers import get_logger

from data.feature_repository import FeatureRepository
from domain.exceptions import (ArgumentNullException, FeatureExistsException,
                               FeatureKeyConflictException,
                               FeatureNotFoundException,
                               InvalidFeatureTypeException,
                               InvalidFeatureValueException)
from domain.feature import Feature, FeatureType
from domain.rest import (CreateFeatureRequest, DeleteResponse,
                         EvaluateFeatureResponse, UpdateFeatureRequest)

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

    async def evaluate_feature_update(
        self,
        feature_key: str,
        value: Any
    ) -> EvaluateFeatureResponse:
        '''
        Evaluate a feature
        '''

        ArgumentNullException.if_none_or_whitespace(
            feature_key, 'feature_key')
        ArgumentNullException.if_none_or_whitespace(
            value, 'value')

        logger.info(f'Setting feature {feature_key}: {value}')
        entity = await self.__repository.get({
            'feature_key': feature_key
        })

        if entity is None:
            raise FeatureNotFoundException(
                value_type='key',
                value=feature_key)

        feature = Feature.from_entity(
            data=entity)

        feature.update_feature(
            value=value)

        await self.__repository.replace(
            selector=feature.get_selector(),
            document=feature.to_dict())
        logger.info(f'Updated feature {feature_key}: {value}')

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

        # Validate feature provided is known type
        if not FeatureType.is_known_type(update.feature_type):
            raise InvalidFeatureTypeException(
                feature_type=update.feature_type)

        # Validate feature value is valid for feature type
        if not FeatureType.is_value_valid(
                feature_Type=update.feature_type,
                value=update.value):

            raise InvalidFeatureValueException(
                value=update.value,
                feature_type=update.feature_type)

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

        ArgumentNullException.if_none(create_request, 'create_request')

        logger.info(f'Create feature: {create_request.feature_key}')

        self.__validate_feature_type(
            feature_type=create_request.feature_type,
            value=create_request.value)

        # Feature already exists with given key
        if await self.__repository.feature_key_exists(
                feature_key=create_request.feature_key):

            raise FeatureExistsException(
                feature_key=create_request.feature_key)

        feature = Feature.from_create_feature_request(
            create_request=create_request)

        logger.info(
            f'Created feature: {feature.feature_key}: {feature.feature_id}')

        await self.__repository.insert(
            document=feature.to_dict())

        return feature

    async def update_feature_last_evaluated_date(
        self,
        feature_id: str,
        last_evaluated: datetime
    ) -> Feature:
        logger.info(f'Feature: {feature_id}: Evaluated: {last_evaluated}')

        ArgumentNullException.if_none_or_whitespace(feature_id, 'feature_id')
        ArgumentNullException.if_none(last_evaluated, 'evaluated_date')

        feature = await self.get_feature_by_id(
            feature_id=feature_id)

        # Update the last evaluated date
        feature.last_evaluated = last_evaluated

        update_result = await self.__repository.replace(
            selector=feature.get_selector(),
            document=feature.to_dict())

        logger.info(f'Update result: {update_result.modified_count}')

        return feature

    def __validate_feature_type(
        self,
        feature_type: str,
        value: Any
    ) -> None:
        # Validate feature provided is known type
        if not FeatureType.is_known_type(feature_type):
            raise InvalidFeatureTypeException(
                feature_type=feature_type)

        # Validate feature value is valid for feature type
        if not FeatureType.is_value_valid(
                feature_type=feature_type,
                value=value):

            raise InvalidFeatureValueException(
                value=value,
                feature_type=feature_type)
