"""
A 'Sous Chef' agent that demonstrates the skills pattern with progressive loading.

Most agents stuff all of their domain knowledge into a giant system prompt. This
one keeps the base prompt tiny and stores expert knowledge in separate
`skills/*.md` files. The agent sees only a catalog of skill names and descriptions
at startup, then loads a full skill's instructions on demand through the
`load_skill` tool.

Why this matters:
- The base context stays small, even with many skills.
- Each skill is a focused, well-scoped set of instructions.
- Adding a new skill = dropping a new file in `skills/`. No code changes.
- The agent acts as a router, choosing which expert to consult.
"""

import os
import re
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict

load_dotenv()

# ---------------------------------------------------------------------------
# Skill catalog - load metadata at startup, defer bodies until needed.
# ---------------------------------------------------------------------------

SKILLS_DIR = Path(__file__).parent / "skills"
_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)


def _parse_skill(path: Path) -> dict:
    text = path.read_text()
    match = _FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError(f"Skill {path.name} is missing YAML frontmatter")
    fm, body = match.groups()
    meta = {}
    for line in fm.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip()
    if "name" not in meta or "description" not in meta:
        raise ValueError(
            f"Skill {path.name} needs 'name' and 'description' in frontmatter"
        )
    return {
        "name": meta["name"],
        "description": meta["description"],
        "body": body.strip(),
    }


def _load_catalog() -> dict[str, dict]:
    catalog: dict[str, dict] = {}
    for path in sorted(SKILLS_DIR.glob("*.md")):
        skill = _parse_skill(path)
        catalog[skill["name"]] = skill
    if not catalog:
        raise RuntimeError(f"No skills found in {SKILLS_DIR}")
    return catalog


CATALOG = _load_catalog()
print(f"Loaded skill catalog: {', '.join(CATALOG)}")


# ---------------------------------------------------------------------------
# Tool - progressive loading of a specific skill's instructions
# ---------------------------------------------------------------------------


@tool
def load_skill(name: str) -> str:
    """Load the full instructions for one of your skills.

    Call this before answering a domain-specific question. The catalog of
    available skill names is in your system prompt. The returned text is the
    expert instructions you should follow when responding.

    Args:
        name: The exact skill name from the catalog (e.g. "recipe-finder").
    """
    if name not in CATALOG:
        available = ", ".join(CATALOG)
        return f"Unknown skill '{name}'. Available skills: {available}."
    return CATALOG[name]["body"]


tools = [load_skill]


# ---------------------------------------------------------------------------
# LLM and system prompt - catalog summary only, no skill bodies
# ---------------------------------------------------------------------------


def _build_catalog_summary() -> str:
    return "\n".join(
        f"- {name}: {skill['description']}" for name, skill in CATALOG.items()
    )


SYSTEM_PROMPT = f"""You are Sous Chef, a warm and practical cooking assistant.

You don't carry all of your expert knowledge in this prompt. Instead, you have
a catalog of *skills* - focused sets of instructions stored separately. You
load a skill's full instructions on demand using the `load_skill` tool.

Your skill catalog:

{_build_catalog_summary()}

How to work:
1. Read the user's message. Decide which skill (if any) is most relevant.
2. If you need expert guidance for the task, call `load_skill(name)` to fetch
   it. The returned instructions take precedence over your general intuition.
3. Follow those instructions to answer.
4. For small talk, simple clarifying questions, or meta questions about your
   abilities, answer directly without loading a skill.

If a request spans multiple skills, load them one at a time as you need them.
Don't pre-load everything - that defeats the point of progressive loading.
"""


llm = ChatOpenAI(
    base_url=os.environ["OPENAI_ENDPOINT"],
    model="gpt-5.4-mini",
    temperature=0,
)
llm_with_tools = llm.bind_tools(tools)


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------


class State(TypedDict):
    messages: Annotated[list, add_messages]


def call_model(state: State):
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


def should_continue(state: State):
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END


tool_node = ToolNode(tools)

builder = StateGraph(State)
builder.add_node("agent", call_model)
builder.add_node("tools", tool_node)

builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
builder.add_edge("tools", "agent")

# This is what langgraph dev picks up from langgraph.json
graph = builder.compile()
