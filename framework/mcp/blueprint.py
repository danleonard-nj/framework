from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urlparse

from mcp.server.auth.provider import (OAuthAuthorizationServerProvider,
                                      ProviderTokenVerifier, TokenVerifier)
from mcp.server.auth.routes import (build_resource_metadata_url,
                                    create_auth_routes,
                                    create_protected_resource_routes)
from mcp.server.auth.settings import (ClientRegistrationOptions,
                                      RevocationOptions)
from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from pydantic import AnyHttpUrl
from quart import Blueprint
from starlette.routing import Route, Router

from framework.auth.wrappers.azure_ad_wrappers import azure_ad_authorization
from framework.auth.wrappers.key_authorization import key_authorization
from framework.exceptions.nulls import ArgumentNullException
from framework.handlers.response_handler_async import response_handler
from framework.mcp.auth import BearerAuth, authenticated_scope
from framework.mcp.bridge import call_asgi

# Path the SDK's Streamable HTTP app routes on internally. Requests are
# presented to it on this path regardless of the rule they arrived on, so the
# public rule is purely a Quart concern
_SDK_PATH = '/mcp'

# GET opens the legacy standalone SSE stream and DELETE ends a legacy session;
# the SDK answers both itself (405 when stateless)
_METHODS = ['GET', 'POST', 'DELETE']

_AS_METADATA_PATH = '/.well-known/oauth-authorization-server'


def _join_rule(url_prefix: Optional[str], rule: str) -> str:
    # Same joining Quart applies when registering a blueprint rule
    if not url_prefix:
        return rule
    if not rule:
        return url_prefix
    return '/'.join((url_prefix.rstrip('/'), rule.lstrip('/')))


def _origin(url: str) -> str:
    parsed = urlparse(str(url))
    return f'{parsed.scheme}://{parsed.netloc}'


class MCPBlueprint(Blueprint):
    '''
    Blueprint serving an `MCPServer` over Streamable HTTP on designated
    routes of a Quart app, alongside its ordinary routes.

    Protocol handling is left entirely to the SDK's own ASGI app; the
    blueprint contributes routing, framework auth and lifecycle.

        mcp_bp = MCPBlueprint('mcp', __name__, server=MCPServer('oura'))
        mcp_bp.with_key_auth('/mcp', key_name='mcp')

        @mcp_bp.tool()
        async def get_sleep(start_date: str, end_date: str): ...

        app.register_blueprint(mcp_bp)

    `stateless_http` defaults to True so any replica can serve any request.
    `transport_security` is the SDK's DNS rebinding guard; its default only
    allows localhost, so set the public host(s) for deployed apps.
    `http_options` passes further arguments to the SDK's
    `streamable_http_app` (e.g. `max_request_body_size`, `event_store`).

    With more than one replica, construct the `MCPServer` with shared
    request state keys (see `framework.mcp.shared_request_state`).

    An `MCPServer` can only be served once per process (its session manager
    runs once), so register a given blueprint on one app.
    '''

    def __init__(
        self,
        name: str,
        import_name: str,
        server: MCPServer,
        json_response: bool = False,
        stateless_http: bool = True,
        transport_security: Optional[TransportSecuritySettings] = None,
        http_options: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ):
        super().__init__(name, import_name, **kwargs)

        ArgumentNullException.if_none(server, 'server')

        self.server = server
        self.asgi_app = server.streamable_http_app(
            streamable_http_path=_SDK_PATH,
            json_response=json_response,
            stateless_http=stateless_http,
            transport_security=transport_security,
            **(http_options or dict()))

        self.record_once(self.__register_lifespan)

    def tool(self, *args, **kwargs):
        '''
        Register an MCP tool (see `MCPServer.tool`)
        '''

        return self.server.tool(*args, **kwargs)

    def resource(self, *args, **kwargs):
        '''
        Register an MCP resource (see `MCPServer.resource`)
        '''

        return self.server.resource(*args, **kwargs)

    def prompt(self, *args, **kwargs):
        '''
        Register an MCP prompt (see `MCPServer.prompt`)
        '''

        return self.server.prompt(*args, **kwargs)

    def __register_lifespan(self, state) -> None:
        # The SDK app's own lifespan never runs when it isn't the root ASGI
        # app, so the session manager (and with it the server lifespan) is
        # run for as long as Quart is serving
        @state.app.while_serving
        async def run_session_manager():
            async with self.server.session_manager.run():
                yield

    def __get_endpoint(self, rule: str):
        return f'__mcp__{rule}'

    def __add_endpoint(self, rule: str, wrappers: List[Callable]):
        ArgumentNullException.if_none_or_whitespace(rule, 'rule')

        async def dispatch():
            return await call_asgi(
                self.asgi_app,
                path=_SDK_PATH,
                scope=authenticated_scope())

        view = dispatch
        for wrapper in reversed(wrappers):
            view = wrapper(view)

        self.add_url_rule(
            rule,
            endpoint=self.__get_endpoint(rule),
            view_func=view,
            methods=_METHODS)

    def __add_app_routes(self, routes: List[Route], public_path: Callable[[str], str]):
        '''
        Serve SDK Starlette routes (OAuth metadata and authorization server
        endpoints) as Quart routes on the app itself. These live at fixed,
        well-known locations, so the blueprint's url_prefix does not apply.
        '''

        self.record_once(
            lambda state: self.__register_app_routes(state, routes, public_path))

    def __register_app_routes(self, state, routes: List[Route], public_path: Callable[[str], str]):
        router = Router(routes=routes)

        for route in routes:
            path = public_path(route.path)

            async def dispatch(_internal=route.path):
                return await call_asgi(router, path=_internal)

            state.app.add_url_rule(
                path,
                endpoint=f'__mcp_oauth__{self.name}__{path}',
                view_func=dispatch,
                methods=sorted(route.methods or ['GET']),
                # The SDK routes answer CORS preflight themselves
                provide_automatic_options=False)

    def configure(self, rule: str, auth_scheme: str) -> None:
        '''
        Serve MCP on `rule` with Azure AD authorization
        '''

        ArgumentNullException.if_none_or_whitespace(auth_scheme, 'auth_scheme')

        self.__add_endpoint(rule, [
            response_handler,
            azure_ad_authorization(scheme=auth_scheme)])

    def with_key_auth(self, rule: str, key_name: str) -> None:
        '''
        Serve MCP on `rule` with API key authorization
        '''

        ArgumentNullException.if_none_or_whitespace(key_name, 'key_name')

        self.__add_endpoint(rule, [
            response_handler,
            key_authorization(name=key_name)])

    def with_bearer(
        self,
        rule: str,
        token_verifier: Optional[TokenVerifier] = None,
        api_key: Optional[str] = None,
        required_scopes: Optional[List[str]] = None,
        authorization_servers: Optional[List[str]] = None,
        base_url: Optional[str] = None,
        resource_server_url: Optional[str] = None,
        resource_name: Optional[str] = None,
        scopes_supported: Optional[List[str]] = None,
        validate_resource: bool = False,
        realm: Optional[str] = None
    ) -> BearerAuth:
        '''
        Serve MCP on `rule` behind bearer token authorization.

        With `authorization_servers`, the endpoint is published as an OAuth
        protected resource (RFC 9728): its metadata document is served and
        401s point to it, which is how clients such as ChatGPT discover
        where to authorize. Use this directly for an external authorization
        server (e.g. Entra ID); `with_oauth` hosts one in the app.

        `resource_server_url` is the endpoint's public URL. It defaults to
        `base_url` (public origin, e.g. https://api.example.com) joined with
        the rule and blueprint prefix, and one of the two is required when
        publishing metadata or validating the token resource.

        `api_key` is additionally accepted as a static bearer credential.
        '''

        ArgumentNullException.if_none_or_whitespace(rule, 'rule')

        auth = BearerAuth(
            token_verifier=token_verifier,
            api_key=api_key,
            required_scopes=required_scopes,
            resource_server_url=resource_server_url,
            validate_resource=validate_resource,
            realm=realm)

        self.__add_endpoint(rule, [response_handler, auth])

        needs_resource_url = bool(authorization_servers) or validate_resource
        if needs_resource_url and not (resource_server_url or base_url):
            raise ValueError(
                'resource_server_url or base_url is required to publish '
                'resource metadata or validate token resources')

        def resolve_resource(state):
            if auth.resource_server_url is None and base_url:
                path = _join_rule(state.url_prefix, rule)
                auth.resource_server_url = f'{base_url.rstrip("/")}{path}'

            if not authorization_servers:
                return

            resource_url = AnyHttpUrl(auth.resource_server_url)
            auth.resource_metadata_url = str(
                build_resource_metadata_url(resource_url))

            routes = create_protected_resource_routes(
                resource_url=resource_url,
                authorization_servers=[AnyHttpUrl(s) for s in authorization_servers],
                scopes_supported=scopes_supported or required_scopes,
                resource_name=resource_name)
            self.__register_app_routes(state, routes, lambda path: path)

        # The public URL depends on the prefix the blueprint is registered
        # with, so it is resolved at registration
        self.record_once(resolve_resource)

        return auth

    def with_oauth(
        self,
        rule: str,
        provider: OAuthAuthorizationServerProvider,
        issuer_url: str,
        required_scopes: Optional[List[str]] = None,
        client_registration_options: Optional[ClientRegistrationOptions] = None,
        revocation_options: Optional[RevocationOptions] = None,
        service_documentation_url: Optional[str] = None,
        resource_server_url: Optional[str] = None,
        resource_name: Optional[str] = None,
        api_key: Optional[str] = None,
        validate_resource: bool = False,
        realm: Optional[str] = None
    ) -> BearerAuth:
        '''
        Serve MCP on `rule` with an OAuth authorization server hosted in the
        app, using the SDK's handlers over `provider`:

            /.well-known/oauth-authorization-server   (RFC 8414)
            /.well-known/oauth-protected-resource/... (RFC 9728)
            /authorize, /token, /register, /revoke

        Endpoint paths sit under `issuer_url`'s path; the metadata paths
        follow the RFC well-known insertion rules. Dynamic client
        registration and revocation are enabled by default, as ChatGPT
        and similar clients cannot be pre-registered. The consent page
        `provider.authorize` redirects to is an ordinary app route.
        '''

        ArgumentNullException.if_none(provider, 'provider')
        ArgumentNullException.if_none_or_whitespace(issuer_url, 'issuer_url')

        if client_registration_options is None:
            client_registration_options = ClientRegistrationOptions(
                enabled=True,
                valid_scopes=required_scopes,
                default_scopes=required_scopes)
        if revocation_options is None:
            revocation_options = RevocationOptions(enabled=True)

        issuer = AnyHttpUrl(issuer_url)
        issuer_path = (urlparse(str(issuer)).path or '').rstrip('/')

        routes = create_auth_routes(
            provider=provider,
            issuer_url=issuer,
            service_documentation_url=(
                AnyHttpUrl(service_documentation_url)
                if service_documentation_url else None),
            client_registration_options=client_registration_options,
            revocation_options=revocation_options)

        def public_path(path: str) -> str:
            # RFC 8414 3: the well-known segment precedes the issuer path
            if path == _AS_METADATA_PATH:
                return f'{_AS_METADATA_PATH}{issuer_path}'
            return f'{issuer_path}{path}'

        self.__add_app_routes(routes, public_path)

        return self.with_bearer(
            rule,
            token_verifier=ProviderTokenVerifier(provider),
            api_key=api_key,
            required_scopes=required_scopes,
            authorization_servers=[str(issuer)],
            base_url=_origin(str(issuer)),
            resource_server_url=resource_server_url,
            resource_name=resource_name,
            scopes_supported=client_registration_options.valid_scopes or required_scopes,
            validate_resource=validate_resource,
            realm=realm)

    def with_auth(self, rule: str, *decorators: Callable) -> None:
        '''
        Serve MCP on `rule` behind custom auth decorators, outermost first.
        Each decorator wraps an async view taking no arguments.
        '''

        ArgumentNullException.if_none_or_empty(decorators, 'decorators')

        self.__add_endpoint(rule, [response_handler, *decorators])

    def open(self, rule: str) -> None:
        '''
        Serve MCP on `rule` without authorization
        '''

        self.__add_endpoint(rule, [response_handler])
