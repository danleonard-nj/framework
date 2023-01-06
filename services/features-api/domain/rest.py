from datetime import datetime
from typing import Any, Dict

from dateutil import parser
from framework.exceptions.nulls import ArgumentNullException
from framework.serialization import Serializable

from domain.exceptions import DateTimeParsingException
from utilities.cardinality import get_cardinality_key


class EvaluateFeatureResponse(Serializable):
    def __init__(
        self,
        feature
    ):
        self.feature_id = feature.feature_id
        self.feature_type = feature.feature_type
        self.value = feature.value


class EvaluateFeatureUpdateRequest(Serializable):
    def __init__(
        self,
        data: Dict
    ):
        self.value = data.get('value')


class UpdateFeatureRequest:
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
        data: Dict
    ):
        self.feature_id = data.get('feature_id')
        self.feature_key = data.get('feature_key')
        self.feature_type = data.get('feature_type')
        self.name = data.get('name')
        self.description = data.get('description')
        self.value = data.get('value')


class CreateFeatureRequest:
    def __init__(
        self,
        data: Dict
    ):
        self.feature_key = data.get('feature_key')
        self.feature_type = data.get('feature_type')
        self.name = data.get('name')
        self.description = data.get('description')
        self.value = data.get('value')


class DeleteResponse(Serializable):
    def __init__(
        self,
        deletd: int
    ):
        self.int


class FeatureLastEvaluatedRequest(Serializable):
    def __init__(
        self,
        feature_id: str,
        last_evaluated: datetime
    ):
        ArgumentNullException.if_none_or_whitespace(feature_id, 'feature_id')
        ArgumentNullException.if_none(last_evaluated, 'last_evaluated')

        self.feature_id = feature_id
        self.last_evaluated = last_evaluated

    @staticmethod
    def from_body(data):
        last_evaluated = data.get('last_evaluated')

        try:
            return FeatureLastEvaluatedRequest(
                feature_id=data.get('feature_id'),
                last_evaluated=parser.parse(last_evaluated))
        except:
            raise DateTimeParsingException(
                datetime_str=last_evaluated)
