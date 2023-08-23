from framework.validators.nulls import none_or_whitespace


class ArgumentNullException(Exception):
    def __init__(self, arg_name, *args: object) -> None:
        super().__init__(f"Argument '{arg_name}' cannot be null")

    @staticmethod
    def if_none(value, arg_name):
        if value is None:
            raise ArgumentNullException(arg_name)

    @staticmethod
    def if_none_or_whitespace(value, arg_name):
        if none_or_whitespace(value):
            raise ArgumentNullException(arg_name)

    @staticmethod
    def if_none_or_empty(value, arg_name):
        if not any(value):
            raise ArgumentNullException(arg_name)


class FeatureNotFoundException(Exception):
    def __init__(self, value_type, value, *args: object) -> None:
        super().__init__(
            f"No feature with the {value_type} '{value}' exists")


class FeatureExistsException(Exception):
    def __init__(self, feature_key, *args: object) -> None:
        super().__init__(
            f"A feature with key '{feature_key}' already exists")


class FeatureKeyConflictException(Exception):
    def __init__(self, feature_key, *args: object) -> None:
        super().__init__(
            f"The key '{feature_key}' is associated with an existing feature")


class InvalidFeatureTypeException(Exception):
    def __init__(self, feature_type, *args: object) -> None:
        supported_types = ', '.join(FeatureType.options())
        super().__init__(
            f"Feature type '{feature_type}' is not a supported feature type.")


class InvalidFeatureValueException(Exception):
    def __init__(self, value, feature_type, *args: object) -> None:
        super().__init__(
            f"The value '{value}' is not valid for feature of type '{feature_type}'")


class DateTimeParsingException(Exception):
    def __init__(self, datetime_str, *args: object) -> None:
        super().__init__(
            f"Failed to parse datetime string '{datetime_str}'")
