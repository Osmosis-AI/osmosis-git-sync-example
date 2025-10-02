import logging
from server import mcp
from tools import *

logger = logging.getLogger(__name__)

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(description='Run MCP Streamable HTTP server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8080, help='Port to listen on')
    args = parser.parse_args()

    mcp.run(transport="http", host=args.host, port=args.port)
