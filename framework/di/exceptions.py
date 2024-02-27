

class RegistrationNotFoundForInstantiationError(Exception):
    def __init__(self, implementation_type, requesting_type):
        super().__init__(
            f"Failed to locate registration for type '{implementation_type.__name__}' when instantiating type '{requesting_type.type_name}'")


class RegistrationNotFoundError(Exception):
    def __init__(self, implementation_type):
        super().__init__(
            f"Failed to locate registration for type '{implementation_type.__name__}'")


class InvalidDependencyChainError(Exception):
    def __init__(self):
        super().__init__(
            "Dependency chain is not valid, check your registration types")


class TransientDependencyInjectionError(Exception):
    def __init__(self, required_type, registration):
        super().__init__(
            f"Cannot inject dependency '{required_type.__name__}' with transient lifetime into singleton '{registration.type_name}'")


class InvalidDependencyChainError(Exception):
    def __init__(self):
        super().__init__(
            "Dependency chain is not valid, check your registration types")
