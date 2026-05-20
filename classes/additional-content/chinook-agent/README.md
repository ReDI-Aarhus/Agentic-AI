# Chinook Agent

A LangGraph agent that queries the Chinook music-store sample database. Built
to demonstrate two patterns from the `static_runtime_context.ipynb` lesson:

1. **Static runtime context** - the path to the SQLite file is passed at
   invoke time and read inside tools via `ToolRuntime[Context]`. The same
   agent works against any copy of Chinook without code changes.
2. **Stateful authorization** - the agent starts as a regular user. A
   `claim_admin` tool flips an `is_admin` flag in *graph state*, which
   unlocks the customer/employee/invoice tables for the rest of the chat.

## Static context vs state - and why both

| | Static context | State |
|---|---|---|
| Set when? | Once, at invoke time | Anywhere, via node/tool updates |
| Mutable? | No | Yes |
| Used here for | `db_path` | `is_admin`, message history |

The DB path is fixed for the run, so it goes in **context**. The admin flag
gets flipped *during* the run by a tool, so it has to live in **state**.
Putting them in the wrong place is a common bug:

- DB path in state → has to be passed in the first message, easy to lose
- is_admin in context → can't be changed once the run starts

## Tools

| Tool | Description | Authorization |
|---|---|---|
| `list_tables` | List available tables | Hides admin-only tables for non-admins |
| `query_db(sql)` | Run a SELECT | Refused if the SQL touches admin-only tables and not admin |
| `claim_admin(password)` | Elevate to admin | Returns a `Command` updating `is_admin` in state |

**Public tables**: Artist, Album, Track, Genre, MediaType, Playlist,
PlaylistTrack

**Admin-only tables**: Customer, Employee, Invoice, InvoiceLine

**Demo admin password**: `chinook`

## Getting started

### 1. Download the Chinook DB

From the project directory:

```bash
curl -L -o data/chinook.db \
  https://github.com/lerocha/chinook-database/raw/master/ChinookDatabase/DataSources/Chinook_Sqlite.sqlite
```

Verify it landed:

```bash
ls -lh data/chinook.db    # ~1 MB
```

### 2. Set up your environment

```bash
cp .env.example .env
```

Fill in:
- `OPENAI_ENDPOINT` - the class proxy / Azure base URL
- `OPENAI_API_KEY` - API key for that endpoint
- `LANGSMITH_API_KEY` - for the LangGraph server (free at
  [smith.langchain.com](https://smith.langchain.com/settings))

### 3. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Start the agent server

```bash
langgraph dev
```

This starts the server at `http://localhost:2024` and prints a Studio URL.

### 5. Invoke with context

In the Studio UI (or any client), provide the static context when invoking:

```json
{
  "db_path": "data/chinook.db"
}
```

The default in the dataclass is already `data/chinook.db`, so leaving it
blank works too as long as you launched `langgraph dev` from this directory.

## Things to try

Watch the tool calls in the Studio - you'll see the authorization logic kick
in mid-conversation:

**Public queries (no admin needed):**
- "What tables can I see?"
- "Who are the top 5 artists by number of albums?"
- "What's the most expensive track in the catalog?"
- "How many genres are there?"

**Admin-gated queries:**
- "How many customers does Chinook have?"
  → query_db is refused, agent tells you to claim_admin first
- "Run claim_admin with password 'wrong'"
  → tool returns failure, is_admin still False
- "Run claim_admin with password 'chinook'"
  → state.is_admin flips to True
- "How many customers does Chinook have?" (again)
  → now succeeds

**Multi-tool:**
- "Show me the public tables, then claim admin with password chinook, then
  tell me which country has the most customers."

## How the auth check works

Inside `query_db`:

```python
if _touches_admin_table(sql) and not state.get("is_admin"):
    return "Permission denied: ..."
```

`state.get("is_admin")` reads the current graph state - flipped earlier by
`claim_admin` returning `Command(update={"is_admin": True})`. The agent
doesn't have to remember whether to allow the query; the tool itself
enforces it on every call.

## Project structure

```
chinook-agent/
  agent.py          # Context dataclass, State, tools, graph
  langgraph.json    # Tells langgraph dev where to find the graph
  requirements.txt  # Python dependencies
  .env.example      # Template for API keys
  data/             # Put chinook.db here
```

## Troubleshooting

**"Chinook DB not found at data/chinook.db"**
You skipped step 1. Re-run the `curl` command and confirm the file lands in
the project's `data/` directory. If you launched `langgraph dev` from a
different directory, pass an absolute path in the context.

**Agent keeps refusing admin queries even after claim_admin**
Check the tool message: did you use the right password (`chinook`)? Also
make sure your client passes the conversation history back on each turn -
without history, state.is_admin resets.

**"Only SELECT statements are allowed."**
This agent is read-only by design. Schema modifications are out of scope -
this is a demo about authorization, not destructive operations.
