from uuid import uuid4

from framework.serialization import Serializable


class FeatureType:
    BOOLEAN = 1
    STRING = 2
    ARRAY = 3

    @classmethod
    def validate_type(cls, _type, value):
        if _type == cls.BOOLEAN:
            if isinstance(value, bool):
                return True
            return False
        if _type == cls.STRING:
            if isinstance(value, str):
                return True
            return False
        if _type == cls.ARRAY:
            if isinstance(value, list):
                return True
            return False
        else:
            raise Exception(f'Unsupported type provided')

    @classmethod
    def parse(cls, _int):
        if _int not in cls.__dict__.values():
            return None
        return cls.__dict__[_int]

    @classmethod
    def is_valid(cls, _int):
        if not isinstance(_int, int):
            raise Exception(f"Feature flag must be of type 'int'")
        if _int in cls.__dict__.values():
            return True
        return False

    @classmethod
    def get_type_name(cls, _int):
        if not cls.is_valid(_int):
            raise Exception(f"'{_int}' is not a valid feature type")
        for key, value in cls.__dict__.items():
            if value == _int:
                return key


class Feature(Serializable):
    def __init__(self, data):
        self.feature_id = data.get('feature_id')
        self.feature_key = data.get('feature_key')
        self.name = data.get('name')
        self.description = data.get('description')
        self.type_id = data.get('type_id')
        self.value = data.get('value')

        self.type_name = FeatureType.get_type_name(
            _int=self.type_id)

    def set_feature_id(self, feature_id=None):
        self.feature_id = feature_id or str(uuid4())
        return self


class RequestModel:
    def validate(self):
        pass


class SetFeatureRequest(RequestModel):
    def __init__(self, data):
        self.value = data.get('value')

    def validate(self):
        return self.value is not None


class CreateFeatureRequest(RequestModel):
    def __init__(self, data):
        self.data = data

    def to_feature(self):
        return Feature(
            data=self.data)

    def validate(self):
        feature = Feature(self.data)

        # All values in feature model are required except
        # feature ID
        for key, value in feature.to_dict().items():
            if key != 'feature_id' and value is None:
                return False

        return True
