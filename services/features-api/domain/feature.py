import uuid
from datetime import datetime
from typing import Any, Dict, List

from framework.serialization import Serializable

from domain.exceptions import ArgumentNullException, InvalidFeatureValueException
from domain.rest import CreateFeatureRequest
from utilities.cardinality import get_cardinality_key


class FeatureType:
    Boolean = 'boolean'
    Text = 'text'
    Json = 'json'

    @classmethod
    def types(
        cls
    ) -> List[str]:
        '''
        Get all valid feature types
        '''

        return [cls.Boolean,
                cls.Text,
                cls.Json]

    @classmethod
    def get_type_map(
        cls
    ) -> Dict[str, type]:
        return {
            cls.Boolean: bool,
            cls.Text: str,
            cls.Json: dict
        }


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
        created_date: datetime,
        modified_date: datetime = None,
    ):
        self.feature_id = feature_id
        self.feature_key = feature_key
        self.feature_type = feature_type
        self.name = name
        self.description = description
        self.value = value
        self.created_date = created_date
        self.modified_date = modified_date

    def update_feature(
        self,
        value: Any
    ):
        '''
        Update the feature value
        '''

        ArgumentNullException.if_none_or_whitespace(
            value, 'value')

        self.__validate_value_type(
            value=value)

        self.value = value
        self.modified_date = datetime.utcnow()

    def get_selector(
        self
    ) -> Dict:
        return {
            'feature_id': self.feature_id
        }

    def is_valid_feature_type(
        self
    ) -> bool:
        '''
        Verify feature type is valid
        '''

        valid_types = FeatureType.types()
        return self.feature_type in valid_types

    def __validate_value_type(
        self,
        value: Any
    ) -> None:
        type_map = FeatureType.get_type_map()
        required = type_map[self.feature_type]

        if not isinstance(value, required):
            raise InvalidFeatureValueException(
                value=value,
                feature_type=self.feature_type)

    @staticmethod
    def from_entity(data):
        return Feature(
            feature_id=data.get('feature_id'),
            feature_key=data.get('feature_key'),
            feature_type=data.get('feature_type'),
            name=data.get('name'),
            description=data.get('description'),
            value=data.get('value'),
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
            created_date=datetime.utcnow())
