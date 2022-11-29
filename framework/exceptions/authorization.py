
class UnauthorizedException(Exception):
    def __init__(self, message='Unauthorized'):
        self.message = message


class AuthorizationException(Exception):
    def __init__(self, message: str):
        self.message = message
