'''
Bearer authorization for MCP endpoints.

MCP clients that discover auth themselves (ChatGPT, Claude) rely on the
401 response: its `WWW-Authenticate` challenge names the protected resource
metadata document (RFC 9728), which names the authorization server, which is
where registration, consent and token exchange happen. The framework's
generic auth wrappers answer 401 without that challenge, so MCP endpoints use
this instead.

A validated token is exposed the same way the SDK's own Starlette auth
middleware does it, so `mcp.server.auth.middleware.auth_context.get_access_token()`
works in tools and request state binds to the caller.
'''

import hmac
import json
import time
from functools import wraps
from typing import Callable, List, Optional

from mcp.server.auth.middleware.auth_context import auth_context_var
from mcp.server.auth.middleware.bearer_auth import AuthenticatedUser
from mcp.server.auth.provider import AccessToken, TokenVerifier
from pydantic import AnyHttpUrl, ValidationError
from quart import Response, request
from starlette.authentication import AuthCredentials

from framework.logger.providers import get_logger

logger = get_logger(__name__)

AUTHORIZATION_HEADER = 'Authorization'
API_KEY_CLIENT_ID = 'api-key'


def get_bearer_credential(authorization: Optional[str]) -> Optional[str]:
    '''
    Credential from an `Authorization: Bearer <credential>` header, if any
    '''

    if not authorization:
        return None
    scheme, _, credential = authorization.partition(' ')
    credential = credential.strip()
    if scheme.lower() != 'bearer' or not credential:
        return None
    return credential


def _normalize_url(url: str) -> Optional[str]:
    # Same comparison as the SDK's bearer backend: scheme/host case and
    # default ports normalized, trailing slash ignored
    try:
        return str(AnyHttpUrl(url)).rstrip('/')
    except ValidationError:
        return None


class BearerAuth:
    '''
    Bearer token policy for an MCP endpoint.

    `token_verifier`        :   SDK `TokenVerifier` (e.g. `ProviderTokenVerifier`
                                over an authorization server provider)
    `api_key`               :   optional static key also accepted as a bearer
                                credential, for clients configured by header
    `required_scopes`       :   scopes every token must carry
    `resource_server_url`   :   public URL of the MCP endpoint
    `validate_resource`     :   reject tokens not issued for `resource_server_url`
                                (RFC 8707); needs the verifier to set `resource`
    `resource_metadata_url` :   advertised in the challenge so clients can
                                discover the authorization server
    `realm`                 :   optional challenge realm
    '''

    def __init__(
        self,
        token_verifier: Optional[TokenVerifier] = None,
        api_key: Optional[str] = None,
        required_scopes: Optional[List[str]] = None,
        resource_server_url: Optional[str] = None,
        validate_resource: bool = False,
        resource_metadata_url: Optional[str] = None,
        realm: Optional[str] = None
    ):
        if token_verifier is None and not api_key:
            raise ValueError('BearerAuth requires a token_verifier, an api_key or both')

        self.token_verifier = token_verifier
        self.api_key = api_key
        self.required_scopes = list(required_scopes or [])
        self.resource_server_url = resource_server_url
        self.validate_resource = validate_resource
        self.resource_metadata_url = resource_metadata_url
        self.realm = realm

    async def authenticate(self, credential: str) -> Optional[AccessToken]:
        '''
        Access token for `credential`, or None when it is not valid here
        '''

        # Static key first: constant time and no store lookup
        if self.api_key and hmac.compare_digest(
                credential.encode(), self.api_key.encode()):
            return AccessToken(
                token=credential,
                client_id=API_KEY_CLIENT_ID,
                scopes=self.required_scopes,
                resource=self.resource_server_url)

        if self.token_verifier is None:
            return None

        access_token = await self.token_verifier.verify_token(credential)
        if access_token is None:
            return None

        if access_token.expires_at and access_token.expires_at < int(time.time()):
            return None

        if self.validate_resource and (
                not access_token.resource or
                not self.resource_server_url or
                _normalize_url(access_token.resource) is None or
                _normalize_url(access_token.resource) != _normalize_url(self.resource_server_url)):
            logger.warning(
                f'Bearer token issued for {access_token.resource!r}, '
                f'not {self.resource_server_url}')
            return None

        return access_token

    def challenge(
        self,
        status: int,
        error: Optional[str] = None,
        description: Optional[str] = None
    ) -> Response:
        '''
        RFC 6750 error response with the resource metadata pointer
        '''

        params = []
        if self.realm:
            params.append(f'realm="{self.realm}"')
        if error:
            params.append(f'error="{error}"')
        if description:
            params.append(f'error_description="{description}"')
        if self.resource_metadata_url:
            params.append(f'resource_metadata="{self.resource_metadata_url}"')

        header = 'Bearer'
        if params:
            header = f'Bearer {", ".join(params)}'

        body = {'error': error or 'invalid_token',
                'error_description': description or 'Authentication required'}

        response = Response(
            json.dumps(body),
            status=status,
            content_type='application/json')
        response.headers['WWW-Authenticate'] = header
        return response

    def __call__(self, function: Callable) -> Callable:
        '''
        Decorate an async view with this policy
        '''

        @wraps(function)
        async def wrapper(*args, **kwargs):
            credential = get_bearer_credential(
                request.headers.get(AUTHORIZATION_HEADER))

            # RFC 6750 3.1: no error code when no credential was offered
            if credential is None:
                return self.challenge(401)

            access_token = await self.authenticate(credential)
            if access_token is None:
                logger.info('MCP request rejected: invalid bearer credential')
                return self.challenge(
                    401, 'invalid_token', 'The access token is invalid or expired')

            for scope in self.required_scopes:
                if scope not in access_token.scopes:
                    return self.challenge(
                        403, 'insufficient_scope', f'Required scope: {scope}')

            token = auth_context_var.set(AuthenticatedUser(access_token))
            try:
                return await function(*args, **kwargs)
            finally:
                auth_context_var.reset(token)

        return wrapper


def authenticated_scope() -> dict:
    '''
    ASGI scope entries for the caller authenticated by `BearerAuth`, in the
    form the SDK's Starlette auth middleware leaves them
    '''

    user = auth_context_var.get()
    if user is None:
        return dict()
    return {'user': user, 'auth': AuthCredentials(user.scopes)}
