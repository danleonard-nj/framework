from flask import request
from deprecated import deprecated

from framework.exceptions.authorization import UnauthorizedException


@deprecated
def get_bearer() -> str:
    authorization_header = request.headers.get('Authorization')
    if authorization_header is not None and authorization_header is not '':
        return authorization_header.split(' ')[1]
    else:
        raise UnauthorizedException('Invalid token provided')


@deprecated
def get_auth_key(configuration, keyvault_client):
    certificate_name = configuration.security.certificate_name
    if not certificate_name:
        raise ValueError('Certificate name cannot be null')
    public_key = keyvault_client.get_certificate_public_key(
        certificate_name=certificate_name)
    return public_key
