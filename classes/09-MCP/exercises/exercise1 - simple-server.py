"""
Exercise 1 - Simple MCP Server

Build a minimal MCP server with tools, a resource, and a prompt.

To test with MCP Inspector:
    npx @modelcontextprotocol/inspector uv run python "exercise1 - simple-server.py"
"""

from fastmcp import FastMCP

mcp = FastMCP(
    name="My First MCP Server",
    instructions="A simple MCP server for learning the basics",
)

# =============================================================================
# TOOLS - Functions that can be called by the client
# =============================================================================


@mcp.tool()
def hello(name: str) -> str:
    """Say hello to someone.

    Args:
        name: The name of the person to greet
    """
    # TODO: Return a greeting like "Hello, {name}!"
    # Validate that name is not empty (raise ValueError if it is)
    pass


@mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers together.

    Args:
        a: First number
        b: Second number
    """
    # TODO: Return the sum of a and b
    pass


# =============================================================================
# RESOURCE - Data source that can be accessed by the client
# =============================================================================


@mcp.resource("info://server")
def get_server_info() -> str:
    """Provides information about this MCP server."""
    # TODO: Return a string describing the server and its capabilities
    # e.g. "My First MCP Server - provides greeting and math tools"
    pass


# =============================================================================
# PROMPT - Template for common interactions
# =============================================================================


@mcp.prompt()
def greeting_prompt(name: str = "World") -> str:
    """Generate a prompt that asks the LLM to greet someone.

    Args:
        name: The name to greet (default: "World")
    """
    # TODO: Return a prompt string like
    # "Please greet {name} warmly and wish them a great day."
    pass


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    mcp.run(transport="stdio")
