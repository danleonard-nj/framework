import uuid
from datetime import datetime
from typing import Any, Dict, List

from framework.exceptions.nulls import ArgumentNullException
from framework.serialization import Serializable

from domain.exceptions import (InvalidFeatureTypeException,
                               InvalidFeatureValueException)
from domain.rest import CreateFeatureRequest
from utilities.cardinality import get_cardinality_key


class FeatureType:
    Boolean = 'boolean'
    Number = 'number'
    Text = 'text'
    Json = 'json'

    @classmethod
    def options(
        cls
    ) -> List[str]:
        '''
        Get all known valid feature type
        option
        '''

        return [cls.Boolean,
                cls.Number,
                cls.Text,
                cls.Json]

    @classmethod
    def is_known_type(
        cls,
        feature_type: str
    ):
        '''
        Verify a feature type is known and
        valid
        '''

        ArgumentNullException.if_none_or_whitespace(
            feature_type, 'feature_type')

        return feature_type in cls.options()

    @classmethod
    def get_type_mapping(
        cls
    ) -> Dict[str, type]:
        '''
        Get the allowed system types mapping
        given all feature types
        '''

        return {
            cls.Boolean: [bool],
            cls.Text: [str],
            cls.Json: [dict],
            cls.Number: [float, int]
        }

    @classmethod
    def get_types(
        cls,
        feature_type: str
    ) -> Dict[str, type]:
        '''
        Get the allowed system types for a
        given feature type
        '''

        ArgumentNullException.if_none_or_whitespace(
            feature_type, 'feature_type')

        if not cls.is_known_type(
                feature_type=feature_type):
            raise InvalidFeatureTypeException(
                feature_type=feature_type)

        mapping = cls.get_type_mapping()
        return mapping[feature_type]

    @classmethod
    def is_value_valid(
        cls,
        feature_type: str,
        value: Any
    ) -> bool:

        ArgumentNullException.if_none_or_whitespace(
            feature_type, 'feature_type')
        ArgumentNullException.if_none(
            value, 'value')

        if not cls.is_known_type(
                feature_type=feature_type):
            raise InvalidFeatureTypeException(
                feature_type=feature_type)

        mapped_types = cls.get_types(
            feature_type=feature_type)

        for mapped_type in mapped_types:
            if isinstance(value, mapped_type):
                return True

        return False


class Feature(Serializable):
    @property
    def cardinality_key(
        self
    ):
        return get_cardinality_key(
            self.feature_key,
            self.feature_type,
            self.name,
            self.description,
            self.value)

    def __init__(
        self,
        feature_id: str,
        feature_key: str,
        feature_type: str,
        name: str,
        description: str,
        value: Any,
        last_evaluated: datetime,
        created_date: datetime,
        modified_date: datetime = None,
    ):
        self.feature_id = feature_id
        self.feature_key = feature_key
        self.feature_type = feature_type
        self.name = name
        self.description = description
        self.value = value
        self.last_evaluated = last_evaluated
        self.created_date = created_date
        self.modified_date = modified_date

        self.__validate()

    def __validate(
        self
    ):
        if not FeatureType.is_known_type(
                feature_type=self.feature_type):
            raise InvalidFeatureTypeException(
                feature_type=self.feature_type)

        if not FeatureType.is_value_valid(
                feature_type=self.feature_type,
                value=self.value):
            raise InvalidFeatureValueException(
                value=self.value,
                feature_type=self.feature_type)

    def update_feature(
        self,
        value: Any
    ):
        '''
        Update the feature value
        '''

        ArgumentNullException.if_none_or_whitespace(
            value, 'value')

        FeatureType.is_value_valid(
            feature_type=self.feature_type,
            value=value)

        self.value = value
        self.modified_date = datetime.utcnow()

    def get_selector(
        self
    ) -> Dict:
        return {
            'feature_id': self.feature_id
        }

    @staticmethod
    def from_entity(data):
        return Feature(
            feature_id=data.get('feature_id'),
            feature_key=data.get('feature_key'),
            feature_type=data.get('feature_type'),
            name=data.get('name'),
            description=data.get('description'),
            value=data.get('value'),
            last_evaluated=data.get('last_evaluated'),
            modified_date=data.get('modified_date'),
            created_date=data.get('created_date'))

    @staticmethod
    def from_create_feature_request(
        create_request: CreateFeatureRequest
    ):
        return Feature(
            feature_id=str(uuid.uuid4()),
            feature_key=create_request.feature_key,
            feature_type=create_request.feature_type,
            name=create_request.name,
            description=create_request.description,
            value=create_request.value,
            created_date=datetime.utcnow(),
            last_evaluated=datetime.utcnow())
