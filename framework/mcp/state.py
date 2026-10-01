from typing import List, Optional, Union

from mcp.server.mcpserver import RequestStateSecurity

from framework.exceptions.nulls import ArgumentNullException

Secret = Union[str, bytes]


def shared_request_state(
    secrets: Union[Secret, List[Secret]],
    audience: str,
    ttl: float = 600.0
) -> RequestStateSecurity:
    '''
    Request state protection shared by every replica of a service.

    `MCPServer` defaults to a key generated per process, so state issued by
    one replica (e.g. an input-required round trip) is rejected by another.
    Pass the result as `MCPServer(request_state_security=...)` with a secret
    from configuration (at least 32 characters). List several secrets to
    rotate: the first seals, all of them open.

    `audience` separates services sharing a secret; use the server name.
    '''

    ArgumentNullException.if_none(secrets, 'secrets')
    ArgumentNullException.if_none_or_whitespace(audience, 'audience')

    if isinstance(secrets, (str, bytes)):
        secrets = [secrets]

    return RequestStateSecurity(
        keys=secrets,
        ttl=ttl,
        audience=audience)
