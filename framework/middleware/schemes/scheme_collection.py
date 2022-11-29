
from middleware.schemes.authorization_scheme import AuthorizationScheme


class SchemeCollection:
    def __init__(self):
        self._schemes = []

    def register_scheme(self, scheme: AuthorizationScheme) -> None:
        self._schemes.append(scheme)
