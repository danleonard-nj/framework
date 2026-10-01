'''
MCP support for Quart apps. Requires the `mcp` extra:

    pip install framework[mcp]
'''

from framework.mcp.auth import BearerAuth
from framework.mcp.blueprint import MCPBlueprint
from framework.mcp.bridge import call_asgi
from framework.mcp.state import shared_request_state

__all__ = ['BearerAuth', 'MCPBlueprint', 'call_asgi', 'shared_request_state']
