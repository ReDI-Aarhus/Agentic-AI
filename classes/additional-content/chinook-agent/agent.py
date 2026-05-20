"""
A LangGraph agent that queries the Chinook sample SQLite database.

Demonstrates two patterns from class:

1. **Static runtime context** (`08-rag/code/static_runtime_context.ipynb`) -
   the path to the SQLite file is passed as immutable context at invoke time.
   Tools read it via `runtime.context.db_path`. The same agent can run
   against any copy of Chinook without code changes.

2. **Stateful authorization** - the run starts as a regular user with
   read-only access to public tables. A `claim_admin` tool flips an
   `is_admin` flag in *graph state* (via `Command(update={...})`), which
   unlocks the customer/employee/invoice tables for the rest of the chat.
   The flag lives in state (mutable), not context (immutable), because it
   changes mid-run.

Get the Chinook DB:

    curl -L -o data/chinook.db \\
      https://github.com/lerocha/chinook-database/raw/master/ChinookDatabase/DataSources/Chinook_Sqlite.sqlite
"""

import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.types import Command
from typing_extensions import TypedDict

load_dotenv()


# ---------------------------------------------------------------------------
# Static runtime context - set once per invoke, never changes during the run
# ---------------------------------------------------------------------------


@dataclass
class Context:
    db_path: str = "data/chinook.db"


# ---------------------------------------------------------------------------
# Mutable graph state
# ---------------------------------------------------------------------------


class State(TypedDict):
    messages: Annotated[list, add_messages]
    is_admin: bool


# ---------------------------------------------------------------------------
# Authorization rules
# ---------------------------------------------------------------------------

ADMIN_ONLY_TABLES = {"Customer", "Employee", "Invoice", "InvoiceLine"}
PUBLIC_TABLES = {
    "Artist",
    "Album",
    "Track",
    "Genre",
    "MediaType",
    "Playlist",
    "PlaylistTrack",
}
ADMIN_PASSWORD = "chinook"


def _open_conn(db_path: str) -> sqlite3.Connection:
    if not Path(db_path).exists():
        raise FileNotFoundError(
            f"Chinook DB not found at {db_path}. See README for how to download it."
        )
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _touches_admin_table(sql: str) -> bool:
    upper = sql.upper()
    return any(t.upper() in upper for t in ADMIN_ONLY_TABLES)


# ---------------------------------------------------------------------------
# Tools - all three read static context and/or graph state via `runtime`.
# ---------------------------------------------------------------------------


@tool
def list_tables(runtime: ToolRuntime[Context]) -> str:
    """List the tables in the Chinook database.

    Non-admin callers see only the public tables. Admins see everything.
    """
    with _open_conn(runtime.context.db_path) as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
    all_tables = [r["name"] for r in rows]
    if runtime.state.get("is_admin"):
        return f"All tables: {', '.join(all_tables)}"
    visible = [t for t in all_tables if t not in ADMIN_ONLY_TABLES]
    hidden = len(all_tables) - len(visible)
    return (
        f"Public tables: {', '.join(visible)}.\n"
        f"({hidden} admin-only tables hidden - call claim_admin to unlock.)"
    )


@tool
def query_db(sql: str, runtime: ToolRuntime[Context]) -> str:
    """Run a read-only SELECT query against the Chinook DB and return the rows.

    Queries against Customer, Employee, Invoice, or InvoiceLine require
    admin status. Other tables are open to everyone.
    """
    if not sql.strip().upper().startswith("SELECT"):
        return "Only SELECT statements are allowed."

    if _touches_admin_table(sql) and not runtime.state.get("is_admin"):
        return (
            "Permission denied: this query touches an admin-only table "
            "(Customer / Employee / Invoice / InvoiceLine). "
            "Ask the user to call claim_admin first."
        )

    try:
        with _open_conn(runtime.context.db_path) as conn:
            rows = conn.execute(sql).fetchmany(50)
    except sqlite3.Error as e:
        return f"SQL error: {e}"

    if not rows:
        return "(no rows)"

    columns = rows[0].keys()
    header = " | ".join(columns)
    body = "\n".join(" | ".join(str(r[c]) for c in columns) for r in rows)
    note = "\n(truncated to 50 rows)" if len(rows) == 50 else ""
    return f"{header}\n{body}{note}"


@tool
def claim_admin(password: str, runtime: ToolRuntime) -> Command:
    """Claim admin status by providing the admin password.

    On success, the caller can query customer/employee/invoice tables for
    the rest of the conversation. The unlock is written to graph state.
    """
    if password == ADMIN_PASSWORD:
        return Command(
            update={
                "is_admin": True,
                "messages": [
                    ToolMessage(
                        "Admin access granted. Customer, Employee, Invoice, "
                        "and InvoiceLine are now queryable.",
                        tool_call_id=runtime.tool_call_id,
                    )
                ],
            }
        )
    return Command(
        update={
            "messages": [
                ToolMessage(
                    "Wrong password. Admin status unchanged.",
                    tool_call_id=runtime.tool_call_id,
                )
            ]
        }
    )


tools = [list_tables, query_db, claim_admin]


# ---------------------------------------------------------------------------
# LLM and system prompt
# ---------------------------------------------------------------------------


llm = ChatOpenAI(
    base_url=os.environ["OPENAI_ENDPOINT"],
    model="gpt-5.4-mini",
    temperature=0,
)
llm_with_tools = llm.bind_tools(tools)


SYSTEM_PROMPT = f"""You are a SQL assistant for the Chinook music store database.

Tools:
- list_tables: show available tables
- query_db: run a SELECT query
- claim_admin: elevate the current session to admin (needs a password)

The DB has two zones:
- Public (always queryable): {", ".join(sorted(PUBLIC_TABLES))}
- Admin-only: {", ".join(sorted(ADMIN_ONLY_TABLES))}

If the user asks something that requires an admin-only table and they aren't
admin yet, tell them they need to call claim_admin first (point them at the
README for the demo password - don't tell them what it is).

Always run real queries through query_db. Don't guess at numbers or schema.
Keep result samples small (LIMIT 10 unless the user asks otherwise) and
explain the answer in plain language.
"""


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------


def call_model(state: State):
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


def should_continue(state: State):
    last = state["messages"][-1]
    if last.tool_calls:
        return "tools"
    return END


tool_node = ToolNode(tools)

builder = StateGraph(State, context_schema=Context)
builder.add_node("agent", call_model)
builder.add_node("tools", tool_node)
builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
builder.add_edge("tools", "agent")

graph = builder.compile()
