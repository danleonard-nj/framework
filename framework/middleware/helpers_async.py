from quart import request

from framework.exceptions.authorization import UnauthorizedException


def get_bearer() -> str:
    authorization_header = request.headers.get('Authorization')
    if authorization_header is not None and authorization_header is not '':
        return authorization_header.split(' ')[1]
    else:
        raise UnauthorizedException('Invalid token provided')
