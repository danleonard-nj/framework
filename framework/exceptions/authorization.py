from deprecated import deprecated


class UnauthorizedException(Exception):
    def __init__(self, message='Unauthorized'):
        self.message = message


class AuthorizationException(Exception):
    def __init__(self, message: str):
        self.message = message


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


class AuthorizationHeaderException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(
            f"No value provided in request authorization header")
