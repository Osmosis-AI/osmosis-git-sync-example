import asyncio

from fastmcp import Client
from rich import print

async def example():
    client = Client("http://0.0.0.0:8080/mcp")

    # Connection established here
    async with client:
        print(f"Connected: {client.is_connected()}")

        # Make multiple calls within the same session
        tools = await client.list_tools()
        print(tools)

    # Connection closed automatically here
    print(f"Connected: {client.is_connected()}")

if __name__ == "__main__":
    asyncio.run(example())
