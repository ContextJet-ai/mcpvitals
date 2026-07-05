from mcp.server.fastmcp import FastMCP

mcp = FastMCP("reference")


@mcp.tool()
def search_docs(query: str) -> str:
    """Search the documentation for a query and return the top passage."""
    return f"result for {query}"


if __name__ == "__main__":
    mcp.run()
