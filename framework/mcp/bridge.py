'''
Serve an ASGI application from inside a Quart view.

Quart has no equivalent of Starlette's `Mount`, and replacing `app.asgi_app`
would route around Quart entirely (no blueprints, auth wrappers, error
handlers or request context). This helper runs an ASGI app for the current
request instead, so the endpoint behaves like any other Quart route and only
the response body is produced by the foreign app.

Nothing here is MCP-specific.
'''

import asyncio
from typing import Any, Awaitable, Callable, Dict, Optional

from quart import Response, request

ASGIApp = Callable[
    [Dict[str, Any], Callable[[], Awaitable[dict]], Callable[[dict], Awaitable[None]]],
    Awaitable[None]]

# Bounded so a slow client applies backpressure to the app's sends rather
# than letting a long-lived stream buffer without limit
_QUEUE_SIZE = 64


class AsgiBridgeException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


def _consume_result(task: asyncio.Task) -> None:
    # Retrieve the outcome of a task we abandoned so asyncio does not log
    # 'exception was never retrieved' after a disconnect
    if not task.cancelled():
        task.exception()


async def call_asgi(
    app: ASGIApp,
    path: Optional[str] = None,
    scope: Optional[Dict[str, Any]] = None
) -> Response:
    '''
    Run `app` for the current Quart request and return its response.

    `app`   :   ASGI application to dispatch to
    `path`  :   path presented to the app, defaults to the request path.
                Use when the app routes on a fixed path that differs from
                the rule the Quart view is registered on
    `scope` :   extra ASGI scope entries (e.g. `user` / `auth` for apps
                that read an authenticated principal from the scope)
    '''

    overrides = scope
    scope = dict(request.scope)
    if path is not None:
        scope['path'] = path
        scope['raw_path'] = path.encode()
        scope['root_path'] = ''
    if overrides:
        scope.update(overrides)

    # Read through Quart so MAX_CONTENT_LENGTH and BODY_TIMEOUT apply
    body = await request.get_data()

    disconnected = asyncio.Event()
    body_sent = False

    async def receive() -> dict:
        nonlocal body_sent
        if not body_sent:
            body_sent = True
            return {'type': 'http.request', 'body': body, 'more_body': False}

        # Quart cancels the view (and later the body stream) when the
        # client goes away, which is where this is set
        await disconnected.wait()
        return {'type': 'http.disconnect'}

    loop = asyncio.get_running_loop()
    start: asyncio.Future = loop.create_future()
    chunks: asyncio.Queue = asyncio.Queue(maxsize=_QUEUE_SIZE)

    async def send(message: dict) -> None:
        if message['type'] == 'http.response.start':
            start.set_result(message)
        elif message['type'] == 'http.response.body':
            data = message.get('body', b'')
            if data:
                await chunks.put(data)
            if not message.get('more_body', False):
                await chunks.put(None)

    # The task inherits the current context, so request context and any
    # contextvars set by auth wrappers are visible to the app
    task = asyncio.ensure_future(app(scope, receive, send))
    task.add_done_callback(_consume_result)

    def abandon() -> None:
        disconnected.set()
        if not task.done():
            task.cancel()

    try:
        await asyncio.wait({start, task}, return_when=asyncio.FIRST_COMPLETED)
    except BaseException:
        abandon()
        raise

    if not start.done():
        # App returned or raised without starting a response
        task.result()
        raise AsgiBridgeException('ASGI app completed without sending a response')

    async def stream():
        completed = False
        try:
            while True:
                chunk = await chunks.get()
                if chunk is None:
                    completed = True
                    return
                yield chunk
        finally:
            if completed:
                disconnected.set()
            else:
                abandon()

    message = start.result()
    headers = [(k.decode('latin-1'), v.decode('latin-1'))
               for k, v in message.get('headers', [])]
    response = Response(
        stream(),
        status=message['status'],
        headers=headers)

    # Quart applies its default mimetype when none is given; keep the
    # app's headers as sent (e.g. a bare 202 has no content type)
    if not any(k.lower() == 'content-type' for k, _ in headers):
        del response.headers['Content-Type']

    # Streams (SSE) outlive RESPONSE_TIMEOUT; the app owns its own keepalive
    response.timeout = None
    return response
