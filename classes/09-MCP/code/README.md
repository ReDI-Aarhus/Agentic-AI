# MCP (Model Context Protocol) Examples

This directory contains examples and exercises for working with the Model Context Protocol (MCP).

## Contents

### Exercise 2: LangChain MCP Integration (`exercise2 - langchain-mcp.ipynb`)

A comprehensive notebook demonstrating how to use MCP servers with LangChain and LangGraph:

- **MCP Core Concepts**: Understanding Tools, Resources, and Prompts
- **Stdio Transport**: Connecting to local MCP servers (npm packages, Python scripts)
- **HTTP/SSE Transport**: Understanding remote MCP server connections
- **LangGraph Integration**: Creating agents with MCP tools using `create_react_agent`
- **Resources and Prompts**: Loading and using MCP resources and prompts in LangChain workflows
- **Custom Server Integration**: Connecting to your own MCP server from Exercise 1

### Exercise 1: Build a Simple MCP Server (`exercises/exercise1 - simple-server.py`)

Student exercise to build a custom MCP server with tools, resources, and prompts. See `exercises/exercise1 - simple-server.md` for instructions.

### Sample Server (`sample-server.py`)

The `sample-server.py` demonstrates a complete reference MCP server implementation with:

### Features

- **Tools**: Functions that can be called by MCP clients
  - `add_numbers`: Add two numbers together
  - `calculate_circle_area`: Calculate circle area and circumference
  - `get_current_time`: Get the current date and time

- **Resources**: Data sources that can be accessed
  - `config://settings`: Server configuration information
  - `docs://readme`: Server documentation
  - `data://sample`: Sample data with user records

- **Prompts**: Templates for common interactions
  - `greeting`: Generate a personalized greeting message
  - `math_help`: Get help with mathematical operations

### Setup

1. Install the required dependencies:
```bash
pip install fastmcp
```

2. Run the server:
```bash
python sample-server.py
```

The server uses **Stdio transport**, which means it communicates via standard input/output, making it suitable for integration with MCP clients.

### Usage

The server is designed to be used with MCP-compatible clients. When running, it will:
- Accept commands via stdin
- Send responses via stdout
- Provide access to all registered tools, resources, and prompts

### Architecture

The sample server is built using **FastMCP**, a Python framework for creating MCP servers quickly and easily. Key components:

- **Tools** are decorated with `@mcp.tool()` and define callable functions
- **Resources** are decorated with `@mcp.resource(uri)` and provide data access
- **Prompts** are decorated with `@mcp.prompt()` and define interaction templates

## Transport Types

### Stdio Transport

Most MCP servers use **stdio transport**, which means they communicate via standard input/output. This is suitable for:
- Local processes
- npm packages distributed via `npx`
- Python scripts run locally
- Automatic lifecycle management (server starts when needed)

**Example configuration:**
```python
{
    "time": {
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "@theo.foobar/mcp-time"]
    }
}
```

### HTTP/SSE Transport

MCP also supports **HTTP with Server-Sent Events** for remote servers:
- Web-based MCP servers
- Servers running on different machines
- Persistent server instances

**Example configuration:**
```python
{
    "my_server": {
        "transport": "sse",
        "url": "http://localhost:8000/sse"
    }
}
```

## Getting Started

1. **Try the sample server:**
   ```bash
   npx @modelcontextprotocol/inspector uv run python 6-mcp/sample-server.py
   ```

2. **Complete Exercise 1:** Build your own MCP server by following `exercises/exercise1 - simple-server.md`

3. **Learn LangChain integration:** Work through `exercise2 - langchain-mcp.ipynb` to see how to use MCP servers with LangChain agents

### References

- [FastMCP Documentation](https://gofastmcp.com)
- [MCP Specification](https://modelcontextprotocol.io)
- [LangChain MCP Server](https://github.com/langchain-ai/langchain-mcp)
