

def _type_name(value: type | str) -> str:
    return value if isinstance(value, str) else value.__name__


class RegistrationNotFoundForInstantiationError(Exception):
    def __init__(
        self,
        implementation_type: type | str,
        requesting_type,
    ):
        super().__init__(
            f"Failed to locate registration for type "
            f"'{_type_name(implementation_type)}' when instantiating type "
            f"'{requesting_type.type_name}'"
        )


class RegistrationNotFoundError(Exception):
    def __init__(self, implementation_type: type | str):
        super().__init__(
            f"Failed to locate registration for type "
            f"'{_type_name(implementation_type)}'"
        )


class InvalidDependencyChainError(Exception):
    def __init__(self):
        super().__init__(
            "Dependency chain is not valid, check your registration types"
        )


class TransientDependencyInjectionError(Exception):
    def __init__(
        self,
        required_type: type | str,
        registration,
    ):
        super().__init__(
            f"Cannot inject dependency '{_type_name(required_type)}' "
            f"with transient lifetime into singleton "
            f"'{registration.type_name}'"
        )