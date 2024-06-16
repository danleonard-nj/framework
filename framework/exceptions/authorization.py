from deprecated import deprecated
from framework.exceptions.rest import HttpException


class UnauthorizedException(HttpException):
    def __init__(self, message='Unauthorized'):
        super().__init__(message, 401)


class AuthorizationException(HttpException):
    def __init__(self, message: str):
        super().__init__(message, 401)


@deprecated
class AuthorizationScopeException(Exception):
    def __init__(self, scope, *args: object) -> None:
        super().__init__(
            f"Could not find required scope '{scope}' in the provided access token")


@deprecated
class AuthorizationSchemeException(Exception):
    def __init__(self, scope, *args: object) -> None:
        super().__init__(
            f"No authorization scheme with the name '{scope}' is defined")


@deprecated
class AuthorizationHeaderException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(
            f"No value provided in request authorization header")
