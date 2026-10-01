import asyncio
import unittest

import anyio
import httpx2
import uvicorn
from mcp import Client
from mcp.client.streamable_http import streamable_http_client
from mcp.server.mcpserver import Context, MCPServer
from quart import Quart, request

from framework.abstractions.abstract_request import RequestContextProvider
from framework.exceptions.authorization import UnauthorizedException
from framework.mcp import MCPBlueprint

API_KEY = 'test-key'


def require_test_key(function):
    async def wrapper(*args, **kwargs):
        if request.headers.get('x-api-key') != API_KEY:
            raise UnauthorizedException()
        return await function(*args, **kwargs)
    return wrapper


class ToolState:
    def __init__(self):
        self.slow_started = asyncio.Event()
        self.slow_cancelled = asyncio.Event()


def build_app(state: ToolState, **blueprint_kwargs) -> Quart:
    server = MCPServer('test', version='1.0.0')

    @server.tool()
    async def add(a: int, b: int) -> int:
        return a + b

    @server.tool()
    async def count(ctx: Context, steps: int) -> str:
        for step in range(steps):
            await ctx.report_progress(step + 1, steps)
            await asyncio.sleep(0.01)
        return 'done'

    @server.tool()
    async def slow() -> str:
        state.slow_started.set()
        try:
            await asyncio.sleep(30)
        except asyncio.CancelledError:
            state.slow_cancelled.set()
            raise
        return 'finished'

    app = Quart(__name__)
    RequestContextProvider.initialize_provider(app)

    @app.route('/api/ping')
    async def ping():
        return {'ok': True}

    open_bp = MCPBlueprint('mcp', __name__, server=server, **blueprint_kwargs)
    open_bp.open('/mcp')
    app.register_blueprint(open_bp)

    return app


def build_guarded_app() -> Quart:
    app = Quart(__name__)
    RequestContextProvider.initialize_provider(app)

    bp = MCPBlueprint('guarded', __name__, server=MCPServer('guarded'), url_prefix='/tools')
    bp.with_auth('/mcp', require_test_key)

    @bp.tool()
    async def echo(value: str) -> str:
        return value

    app.register_blueprint(bp)
    return app


class UvicornTestCase(unittest.IsolatedAsyncioTestCase):
    async def serve(self, app: Quart) -> str:
        config = uvicorn.Config(app, host='127.0.0.1', port=0, log_level='warning', lifespan='on')
        self.server = uvicorn.Server(config)
        self.server_task = asyncio.ensure_future(self.server.serve())
        while not self.server.started:
            await asyncio.sleep(0.01)
        port = self.server.servers[0].sockets[0].getsockname()[1]
        return f'http://127.0.0.1:{port}'

    async def asyncTearDown(self):
        if hasattr(self, 'server'):
            self.server.should_exit = True
            await asyncio.wait_for(self.server_task, 10)


class MCPBlueprintTests(UvicornTestCase):
    async def asyncSetUp(self):
        self.state = ToolState()
        self.base = await self.serve(build_app(self.state))

    async def test_modern_client_lists_and_calls_tools(self):
        async with Client(f'{self.base}/mcp') as client:
            self.assertTrue(client.protocol_version.startswith('2026'))

            tools = await client.list_tools()
            self.assertEqual({'add', 'count', 'slow'}, {t.name for t in tools.tools})

            result = await client.call_tool('add', {'a': 2, 'b': 3})
            self.assertFalse(result.is_error)
            self.assertEqual('5', result.content[0].text)

    async def test_legacy_client_calls_tools(self):
        async with Client(f'{self.base}/mcp', mode='legacy') as client:
            result = await client.call_tool('add', {'a': 1, 'b': 1})
            self.assertEqual('2', result.content[0].text)

    async def test_progress_streams_over_sse(self):
        updates = []

        async def on_progress(progress, total, message):
            updates.append(progress)

        async with Client(f'{self.base}/mcp') as client:
            result = await client.call_tool('count', {'steps': 3}, progress_callback=on_progress)

        self.assertEqual('done', result.content[0].text)
        self.assertEqual([1, 2, 3], updates)

    async def test_client_disconnect_cancels_tool(self):
        async with Client(f'{self.base}/mcp') as client:
            with anyio.move_on_after(1):
                await client.call_tool('slow', {})

        self.assertTrue(self.state.slow_started.is_set())
        await asyncio.wait_for(self.state.slow_cancelled.wait(), 5)

    async def test_other_routes_are_unaffected(self):
        async with httpx2.AsyncClient() as http:
            response = await http.get(f'{self.base}/api/ping')

        self.assertEqual(200, response.status_code)
        self.assertEqual({'ok': True}, response.json())

    async def test_modern_get_is_rejected(self):
        async with httpx2.AsyncClient() as http:
            response = await http.get(
                f'{self.base}/mcp',
                headers={'accept': 'text/event-stream', 'mcp-protocol-version': '2026-07-28'})

        self.assertEqual(405, response.status_code)

    async def test_legacy_get_opens_event_stream(self):
        async with httpx2.AsyncClient() as http:
            async with http.stream(
                    'GET', f'{self.base}/mcp', headers={'accept': 'text/event-stream'}) as response:
                self.assertEqual(200, response.status_code)
                self.assertEqual('text/event-stream', response.headers['content-type'])

    async def test_hostile_host_is_rejected(self):
        async with httpx2.AsyncClient() as http:
            response = await http.post(
                f'{self.base}/mcp',
                headers={'host': 'evil.example', 'accept': 'application/json, text/event-stream',
                         'content-type': 'application/json'},
                content=b'{}')

        self.assertEqual(421, response.status_code)


class GuardedMCPBlueprintTests(UvicornTestCase):
    async def asyncSetUp(self):
        self.base = await self.serve(build_guarded_app())

    async def test_missing_key_is_unauthorized(self):
        async with httpx2.AsyncClient() as http:
            response = await http.post(
                f'{self.base}/tools/mcp',
                headers={'accept': 'application/json, text/event-stream',
                         'content-type': 'application/json'},
                content=b'{}')

        self.assertEqual(401, response.status_code)

    async def test_key_authorizes_client(self):
        http = httpx2.AsyncClient(headers={'x-api-key': API_KEY})
        transport = streamable_http_client(f'{self.base}/tools/mcp', http_client=http)
        async with http, Client(transport) as client:
            result = await client.call_tool('echo', {'value': 'hi'})

        self.assertEqual('hi', result.content[0].text)


if __name__ == '__main__':
    unittest.main()
