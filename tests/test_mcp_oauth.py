'''
OAuth for MCP endpoints, exercised the way ChatGPT connects: an
unauthenticated call, discovery through the 401 challenge and the metadata
documents, dynamic client registration, a browser consent step, PKCE code
exchange and bearer calls. The client side is the SDK's own OAuth client.
'''

import asyncio
import secrets
import socket
import time
import unittest
from urllib.parse import parse_qs, urlparse

import httpx2
import uvicorn
from mcp import Client
from mcp.client.auth import OAuthClientProvider
from mcp.client.streamable_http import streamable_http_client
from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.provider import (AccessToken, AuthorizationCode,
                                      RefreshToken, construct_redirect_uri)
from mcp.server.mcpserver import MCPServer
from mcp.shared.auth import (AuthorizationCodeResult,
                             OAuthClientInformationFull, OAuthClientMetadata,
                             OAuthToken)
from pydantic import AnyUrl
from quart import Quart, redirect, request

from framework.abstractions.abstract_request import RequestContextProvider
from framework.mcp import MCPBlueprint, shared_request_state

SCOPE = 'mcp'
API_KEY = 'static-test-key'
REDIRECT_URI = 'https://chatgpt.com/connector_platform_oauth_redirect'


class InMemoryProvider:
    '''
    Minimal authorization server provider. `authorize` hands off to a
    consent page, as oura-mcp does, rather than approving inline.
    '''

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.clients = {}
        self.pending = {}
        self.codes = {}
        self.access_tokens = {}
        self.refresh_tokens = {}

    async def get_client(self, client_id):
        return self.clients.get(client_id)

    async def register_client(self, client_info: OAuthClientInformationFull):
        self.clients[client_info.client_id] = client_info

    async def authorize(self, client, params):
        txn = secrets.token_urlsafe(16)
        self.pending[txn] = (client, params)
        return f'{self.base_url}/consent?txn={txn}'

    def approve(self, txn: str) -> str:
        client, params = self.pending.pop(txn)
        code = secrets.token_urlsafe(16)
        self.codes[code] = AuthorizationCode(
            code=code,
            scopes=params.scopes or [SCOPE],
            expires_at=time.time() + 300,
            client_id=client.client_id,
            code_challenge=params.code_challenge,
            redirect_uri=params.redirect_uri,
            redirect_uri_provided_explicitly=params.redirect_uri_provided_explicitly,
            resource=params.resource)
        return construct_redirect_uri(str(params.redirect_uri), code=code, state=params.state)

    async def load_authorization_code(self, client, authorization_code):
        return self.codes.get(authorization_code)

    def _issue(self, client_id, scopes, resource) -> OAuthToken:
        access = secrets.token_urlsafe(24)
        refresh = secrets.token_urlsafe(24)
        self.access_tokens[access] = AccessToken(
            token=access, client_id=client_id, scopes=scopes,
            expires_at=int(time.time()) + 3600, resource=resource)
        self.refresh_tokens[refresh] = RefreshToken(
            token=refresh, client_id=client_id, scopes=scopes, resource=resource)
        return OAuthToken(
            access_token=access, expires_in=3600,
            scope=' '.join(scopes), refresh_token=refresh)

    async def exchange_authorization_code(self, client, authorization_code):
        self.codes.pop(authorization_code.code, None)
        return self._issue(client.client_id, authorization_code.scopes, authorization_code.resource)

    async def load_refresh_token(self, client, refresh_token):
        return self.refresh_tokens.get(refresh_token)

    async def exchange_refresh_token(self, client, refresh_token, scopes):
        self.refresh_tokens.pop(refresh_token.token, None)
        return self._issue(client.client_id, scopes or refresh_token.scopes, refresh_token.resource)

    async def load_access_token(self, token):
        return self.access_tokens.get(token)

    async def revoke_token(self, token):
        self.access_tokens.pop(token.token, None)
        self.refresh_tokens.pop(token.token, None)


class MemoryTokenStorage:
    def __init__(self):
        self.tokens = None
        self.client_info = None

    async def get_tokens(self):
        return self.tokens

    async def set_tokens(self, tokens):
        self.tokens = tokens

    async def get_client_info(self):
        return self.client_info

    async def set_client_info(self, client_info):
        self.client_info = client_info


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def build_app(base_url: str, provider: InMemoryProvider, validate_resource: bool) -> Quart:
    server = MCPServer(
        'oauth-test',
        request_state_security=shared_request_state('x' * 32, audience='oauth-test'))

    app = Quart(__name__)
    RequestContextProvider.initialize_provider(app)

    @app.route('/api/ping')
    async def ping():
        return {'ok': True}

    # The consent page is an ordinary app route; a real one asks the owner
    @app.route('/consent')
    async def consent():
        return redirect(provider.approve(request.args['txn']))

    bp = MCPBlueprint('mcp', __name__, server=server, url_prefix='/tools')
    bp.with_oauth(
        '/mcp',
        provider=provider,
        issuer_url=base_url,
        required_scopes=[SCOPE],
        resource_name='OAuth Test',
        api_key=API_KEY,
        validate_resource=validate_resource)

    @bp.tool()
    async def whoami() -> str:
        return get_access_token().client_id

    app.register_blueprint(bp)
    return app


class OAuthTestCase(unittest.IsolatedAsyncioTestCase):
    validate_resource = True

    async def asyncSetUp(self):
        port = free_port()
        self.base = f'http://127.0.0.1:{port}'
        self.mcp_url = f'{self.base}/tools/mcp'
        self.provider = InMemoryProvider(self.base)

        app = build_app(self.base, self.provider, self.validate_resource)
        self.server = uvicorn.Server(uvicorn.Config(
            app, host='127.0.0.1', port=port, log_level='warning', lifespan='on'))
        self.server_task = asyncio.ensure_future(self.server.serve())
        while not self.server.started:
            await asyncio.sleep(0.01)

    async def asyncTearDown(self):
        self.server.should_exit = True
        await asyncio.wait_for(self.server_task, 10)

    def oauth_client(self) -> httpx2.AsyncClient:
        callback = {}

        async def redirect_handler(authorization_url: str):
            # Stand-in for the user's browser: follow /authorize through the
            # app's consent page to the client's redirect URI
            async with httpx2.AsyncClient() as browser:
                response = await browser.get(authorization_url)
                while response.status_code in (302, 303, 307):
                    location = response.headers['location']
                    if location.startswith(REDIRECT_URI):
                        query = parse_qs(urlparse(location).query)
                        callback['code'] = query['code'][0]
                        callback['state'] = query.get('state', [None])[0]
                        return
                    response = await browser.get(location)
                raise AssertionError(f'authorization did not redirect: {response.status_code}')

        async def callback_handler():
            return AuthorizationCodeResult(code=callback['code'], state=callback['state'])

        auth = OAuthClientProvider(
            server_url=self.mcp_url,
            client_metadata=OAuthClientMetadata(
                client_name='ChatGPT',
                redirect_uris=[AnyUrl(REDIRECT_URI)],
                grant_types=['authorization_code', 'refresh_token'],
                response_types=['code'],
                scope=SCOPE),
            storage=MemoryTokenStorage(),
            redirect_handler=redirect_handler,
            callback_handler=callback_handler)

        return httpx2.AsyncClient(auth=auth)


class ChatGPTFlowTests(OAuthTestCase):
    async def test_unauthenticated_call_is_challenged_with_resource_metadata(self):
        async with httpx2.AsyncClient() as http:
            response = await http.post(
                self.mcp_url, content=b'{}',
                headers={'content-type': 'application/json',
                         'accept': 'application/json, text/event-stream'})

        self.assertEqual(401, response.status_code)
        challenge = response.headers['www-authenticate']
        self.assertTrue(challenge.startswith('Bearer'))
        self.assertIn(
            f'resource_metadata="{self.base}/.well-known/oauth-protected-resource/tools/mcp"',
            challenge)
        # RFC 6750: no error code when no credential was presented
        self.assertNotIn('error=', challenge)

    async def test_invalid_token_is_rejected_with_error(self):
        async with httpx2.AsyncClient() as http:
            response = await http.post(
                self.mcp_url, content=b'{}',
                headers={'authorization': 'Bearer nope',
                         'content-type': 'application/json',
                         'accept': 'application/json, text/event-stream'})

        self.assertEqual(401, response.status_code)
        self.assertIn('error="invalid_token"', response.headers['www-authenticate'])

    async def test_metadata_documents(self):
        async with httpx2.AsyncClient() as http:
            resource = (await http.get(
                f'{self.base}/.well-known/oauth-protected-resource/tools/mcp')).json()
            server = (await http.get(
                f'{self.base}/.well-known/oauth-authorization-server')).json()

        self.assertEqual(self.mcp_url, resource['resource'])
        self.assertEqual([f'{self.base}/'], resource['authorization_servers'])
        self.assertEqual([SCOPE], resource['scopes_supported'])

        self.assertEqual(f'{self.base}/authorize', server['authorization_endpoint'])
        self.assertEqual(f'{self.base}/token', server['token_endpoint'])
        self.assertEqual(f'{self.base}/register', server['registration_endpoint'])
        self.assertIn('S256', server['code_challenge_methods_supported'])

    async def test_cors_preflight_is_answered_by_sdk(self):
        async with httpx2.AsyncClient() as http:
            response = await http.options(
                f'{self.base}/token',
                headers={'origin': 'https://inspector.example',
                         'access-control-request-method': 'POST'})

        self.assertEqual(200, response.status_code)
        self.assertIn('access-control-allow-origin', response.headers)

    async def test_full_oauth_flow_then_tool_call(self):
        http = self.oauth_client()
        async with http, Client(streamable_http_client(self.mcp_url, http_client=http)) as client:
            result = await client.call_tool('whoami', {})

        self.assertFalse(result.is_error)
        [registered] = self.provider.clients.values()
        # The tool saw the OAuth principal through the SDK auth context
        self.assertEqual(registered.client_id, result.content[0].text)
        self.assertEqual('ChatGPT', registered.client_name)
        # The token was bound to this resource (RFC 8707)
        [token] = self.provider.access_tokens.values()
        self.assertEqual(self.mcp_url, token.resource)

    async def test_legacy_client_completes_oauth_flow(self):
        http = self.oauth_client()
        transport = streamable_http_client(self.mcp_url, http_client=http)
        async with http, Client(transport, mode='legacy') as client:
            result = await client.call_tool('whoami', {})

        self.assertFalse(result.is_error)

    async def test_static_key_is_still_accepted(self):
        http = httpx2.AsyncClient(headers={'authorization': f'Bearer {API_KEY}'})
        async with http, Client(streamable_http_client(self.mcp_url, http_client=http)) as client:
            result = await client.call_tool('whoami', {})

        self.assertEqual('api-key', result.content[0].text)

    async def test_token_for_another_resource_is_rejected(self):
        self.provider.access_tokens['foreign'] = AccessToken(
            token='foreign', client_id='c', scopes=[SCOPE],
            resource='https://elsewhere.example/mcp')

        async with httpx2.AsyncClient() as http:
            response = await http.post(
                self.mcp_url, content=b'{}',
                headers={'authorization': 'Bearer foreign',
                         'content-type': 'application/json',
                         'accept': 'application/json, text/event-stream'})

        self.assertEqual(401, response.status_code)

    async def test_missing_scope_is_forbidden(self):
        self.provider.access_tokens['narrow'] = AccessToken(
            token='narrow', client_id='c', scopes=['other'], resource=self.mcp_url)

        async with httpx2.AsyncClient() as http:
            response = await http.post(
                self.mcp_url, content=b'{}',
                headers={'authorization': 'Bearer narrow',
                         'content-type': 'application/json',
                         'accept': 'application/json, text/event-stream'})

        self.assertEqual(403, response.status_code)
        self.assertIn('error="insufficient_scope"', response.headers['www-authenticate'])

    async def test_other_routes_stay_open(self):
        async with httpx2.AsyncClient() as http:
            response = await http.get(f'{self.base}/api/ping')

        self.assertEqual(200, response.status_code)


if __name__ == '__main__':
    unittest.main()
