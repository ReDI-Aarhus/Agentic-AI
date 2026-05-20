# Exercise 1 - Build a Simple MCP Server

## Overview

In this exercise you will build a small MCP server using FastMCP. The server will expose tools, a resource, and a prompt. You will test it with the MCP Inspector.

## What You'll Learn

- Creating an MCP server with FastMCP
- The difference between tools, resources, and prompts
- Testing MCP servers with the MCP Inspector

## Setup

Complete the TODO sections in `exercise1 - simple-server.py`.

### Test with MCP Inspector

```bash
npx @modelcontextprotocol/inspector uv run python "exercise1 - simple-server.py"
```

This opens a web interface at http://localhost:5173 where you can test things interactively.

## Tasks

### 1. Implement the `hello` tool

- Return a greeting like `"Hello, Alice!"`
- Raise `ValueError` if name is empty

### 2. Implement the `add` tool

- Return the sum of two numbers

### 3. Implement the `get_server_info` resource

- Return a string describing the server and its capabilities

### 4. Implement the `greeting_prompt` prompt

- Return a prompt string that asks the LLM to greet someone by name

## Testing with Inspector

1. **Tools tab**: Call `hello("Alice")` and `add(3, 5)`. Check that the results are correct.
2. **Resources tab**: Access `info://server`. Confirm it returns your description.
3. **Prompts tab**: Try `greeting_prompt` with a name. Confirm it returns a prompt string.

## Bonus (Optional)

If you finish early, try adding these:

1. A `multiply(a, b)` tool
2. A `docs://usage` resource that returns markdown documentation for the tools
