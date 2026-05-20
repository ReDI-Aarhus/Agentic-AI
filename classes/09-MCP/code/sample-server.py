# npx @modelcontextprotocol/inspector uv run exercises/6-mcp/sample-server.py
# /// script
# dependencies = ["fastmcp[apps]>=3.1"]
# ///
"""
Sample MCP Server with Tools, Resources, and Prompts

This server demonstrates the key features of the Model Context Protocol (MCP):
- Tools: Functions that can be called by the client
- Resources: Data sources that can be accessed
- Resource Templates: Parameterized resources with dynamic URIs
- Prompts: Templates for common interactions
- Apps: Interactive UIs rendered in the conversation (requires `pip install "fastmcp[apps]"`)

The server uses Stdio transport for communication with MCP clients.
"""

from fastmcp import FastMCP
from datetime import datetime
import math
import json

# Create the MCP server instance
mcp = FastMCP(
    name="Sample MCP Server",
    instructions="A demonstration server showing MCP capabilities with tools, resources, and prompts",
)

# =============================================================================
# TOOLS - Functions that can be called by the client
# =============================================================================


@mcp.tool()
def add_numbers(a: float, b: float) -> float:
    """
    Add two numbers together.

    Args:
        a: First number
        b: Second number

    Returns:
        The sum of a and b
    """
    return a + b


@mcp.tool()
def calculate_circle_area(radius: float) -> dict:
    """
    Calculate the area and circumference of a circle given its radius.

    Args:
        radius: The radius of the circle

    Returns:
        Dictionary with area and circumference
    """
    if radius < 0:
        raise ValueError("Radius must be non-negative")

    area = math.pi * radius**2
    circumference = 2 * math.pi * radius

    return {"radius": radius, "area": area, "circumference": circumference}


@mcp.tool()
def get_current_time() -> str:
    """
    Get the current date and time.

    Returns:
        Current date and time as a formatted string
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# =============================================================================
# RESOURCES - Data that can be accessed by the client
# =============================================================================


@mcp.resource("config://settings")
def get_server_settings() -> str:
    """
    Provides the current server configuration settings.
    """
    settings = {
        "server_name": "Sample MCP Server",
        "version": "1.0.0",
        "features": ["tools", "resources", "prompts"],
        "transport": "stdio",
    }
    return json.dumps(settings, indent=2)


@mcp.resource("docs://readme")
def get_readme() -> str:
    """
    Provides documentation about this MCP server.
    """
    return """
    # Sample MCP Server
    
    This is a demonstration MCP server that showcases:
    
    ## Tools Available:
    - add_numbers: Add two numbers
    - calculate_circle_area: Calculate circle properties
    - get_current_time: Get current timestamp
    
    ## Resources Available:
    - config://settings: Server configuration
    - docs://readme: This documentation
    - data://sample: Sample data

    ## Resource Templates (parameterized):
    - users://{user_id}/profile: Get a user's profile (user_id: 1, 2, or 3)
    - logs://{level}: Get logs by severity (debug, info, warning, error)
    
    ## Prompts Available:
    - greeting: Generate a personalized greeting
    - math_help: Get help with math operations
    """


@mcp.resource("data://sample")
def get_sample_data() -> str:
    """
    Provides sample data for testing.
    """
    sample = {
        "users": [
            {"id": 1, "name": "Alice", "role": "developer"},
            {"id": 2, "name": "Bob", "role": "designer"},
            {"id": 3, "name": "Charlie", "role": "manager"},
        ],
        "timestamp": datetime.now().isoformat(),
    }
    return json.dumps(sample, indent=2)


# =============================================================================
# RESOURCE TEMPLATES - Parameterized resources with dynamic URIs
# =============================================================================


@mcp.resource("users://{user_id}/profile")
def get_user_profile(user_id: int) -> str:
    """
    Get profile information for a specific user by ID.

    The URI pattern users://{user_id}/profile allows clients to request
    any user's profile by substituting the user_id parameter.
    """
    users = {
        1: {"id": 1, "name": "Alice", "role": "developer", "team": "Backend"},
        2: {"id": 2, "name": "Bob", "role": "designer", "team": "UX"},
        3: {"id": 3, "name": "Charlie", "role": "manager", "team": "Engineering"},
    }
    user = users.get(user_id)
    if not user:
        return json.dumps({"error": f"User {user_id} not found"})
    return json.dumps(user, indent=2)


@mcp.resource("logs://{level}")
def get_logs_by_level(level: str) -> str:
    """
    Get server logs filtered by severity level.

    Supports: debug, info, warning, error.
    """
    all_logs = [
        {"level": "info", "message": "Server started", "ts": "2025-01-01T10:00:00"},
        {
            "level": "debug",
            "message": "Processing request",
            "ts": "2025-01-01T10:00:01",
        },
        {
            "level": "warning",
            "message": "High memory usage",
            "ts": "2025-01-01T10:05:00",
        },
        {
            "level": "error",
            "message": "Connection timeout",
            "ts": "2025-01-01T10:10:00",
        },
        {"level": "info", "message": "Request completed", "ts": "2025-01-01T10:10:01"},
        {"level": "debug", "message": "Cache miss", "ts": "2025-01-01T10:15:00"},
    ]
    filtered = [log for log in all_logs if log["level"] == level.lower()]
    return json.dumps(filtered, indent=2)


# =============================================================================
# PROMPTS - Templates for common interactions
# =============================================================================


@mcp.prompt()
def greeting(name: str = "User") -> str:
    """
    Generate a personalized greeting message.

    Args:
        name: The name of the person to greet (default: "User")
    """
    return f"""
    Generate a warm and friendly greeting for {name}.
    
    Include:
    - A personalized welcome message
    - A brief introduction to the MCP server capabilities
    - An invitation to try out the available tools
    """


@mcp.prompt()
def math_help(operation: str = "general") -> str:
    """
    Get help with mathematical operations.

    Args:
        operation: The type of math help needed (default: "general")
    """
    return f"""
    Provide assistance with {operation} mathematical operations.
    
    Available math tools:
    - add_numbers: For basic addition
    - calculate_circle_area: For circle geometry calculations
    
    Please explain how to use the relevant tool and provide an example.
    """


# =============================================================================
# APPS - Interactive UIs rendered directly in the conversation
# =============================================================================

from prefab_ui.app import PrefabApp
from prefab_ui.components import Column, Heading, Text, Badge, Row, Separator
from prefab_ui.components.charts import BarChart, ChartSeries


@mcp.tool(app=True)
def team_dashboard() -> PrefabApp:
    """Show an interactive dashboard of team members and project stats."""
    members = [
        {"name": "Alice", "role": "Developer", "tasks": 12},
        {"name": "Bob", "role": "Designer", "tasks": 8},
        {"name": "Charlie", "role": "Manager", "tasks": 5},
    ]

    with Column(gap=4, css_class="p-6 max-w-lg w-full") as view:
        Heading("Team Dashboard")

        BarChart(
            data=members,
            series=[ChartSeries(data_key="tasks", label="Active Tasks")],
            x_axis="name",
            height=200,
        )

        Separator()
        Heading("Team Members", level=3)
        for member in members:
            with Row(gap=2):
                Text(member["name"])
                Badge(member["role"])

    return PrefabApp(view=view)


# =============================================================================
# MAIN - Run the server with Stdio transport
# =============================================================================

if __name__ == "__main__":
    # Run the server using Stdio transport
    # This allows the server to communicate via standard input/output
    mcp.run(transport="stdio")
