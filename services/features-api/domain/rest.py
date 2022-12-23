from typing import Any, Dict
from framework.serialization import Serializable

from utilities.cardinality import get_cardinality_key


class EvaluateFeatureResponse(Serializable):
    def __init__(
        self,
        feature
    ):
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
