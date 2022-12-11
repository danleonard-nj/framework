from framework.validators.nulls import none_or_whitespace


class NullArgumentException(Exception):
    def __init__(self, arg_name, *args: object) -> None:
        super().__init__(f"Argument '{arg_name}' cannot be null")

    @staticmethod
    def if_none(value, arg_name):
        if value is None:
            raise NullArgumentException(arg_name)

    @staticmethod
    def if_none_or_whitespace(value, arg_name):
        if none_or_whitespace(value):
            raise NullArgumentException(arg_name)
