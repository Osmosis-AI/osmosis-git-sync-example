from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import PlainTextResponse

import logging

logger = logging.getLogger(__name__)

mcp = FastMCP("OsmosisTools")

@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> PlainTextResponse:
    return PlainTextResponse("OK")


