"""
A 'Money Mentors' agent that demonstrates multi-agent routing.

Instead of one agent with many tools (like agentchat) or one agent that loads
expert instructions on demand (like sous-chef), this app has THREE separate
specialist agents - budgeting, investing, and tax - and a supervisor that
decides which one should answer each user message.

Why this matters:
- Each specialist has its own focused system prompt and "voice".
- The supervisor picks one specialist per turn using structured output, so the
  routing decision is a typed object you can inspect (not a hidden tool call).
- Every turn re-routes from scratch, so when the user pivots topics the demo
  visibly hops to a different specialist.

Nothing here is real financial advice. It's a teaching demo.
"""

import os
from typing import Annotated, Literal

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

load_dotenv()

# ---------------------------------------------------------------------------
# LLM - shared across supervisor and all specialists. One model, three voices.
# ---------------------------------------------------------------------------

llm = ChatOpenAI(
    base_url=os.environ["OPENAI_ENDPOINT"],
    model="gpt-5.4-mini",
    temperature=0,
)


# ---------------------------------------------------------------------------
# Supervisor - classifies which specialist should handle the latest message.
# Uses structured output so the routing decision is a typed object.
# ---------------------------------------------------------------------------

AgentName = Literal["budgeting", "investing", "tax"]


class Route(BaseModel):
    """The supervisor's decision about which specialist should handle the turn."""

    agent: AgentName = Field(
        description="Which specialist should answer this user message."
    )
    reason: str = Field(
        description="One short sentence explaining why this specialist was picked."
    )


SUPERVISOR_PROMPT = """You are the supervisor of a small team of personal-finance
specialists. For each user message, decide which ONE specialist should answer.

Your team:
- budgeting: spending plans, saving habits, emergency funds, debt payoff, cash flow
- investing: index funds, asset allocation, time horizon, retirement accounts as investments
- tax: deductions, credits, filing, withholding, tax-advantaged accounts as tax shelters

Pick the single best match. If a question straddles two areas, pick the one the
user most needs to hear from first and let the specialist suggest a follow-up.
"""

supervisor_llm = llm.with_structured_output(Route)


def supervisor_node(state):
    decision: Route = supervisor_llm.invoke(
        [SystemMessage(content=SUPERVISOR_PROMPT)] + state["messages"]
    )
    # Surface the routing decision in the chat so students can SEE it happen.
    handoff = AIMessage(
        content=f"_Routing to **{decision.agent}** specialist — {decision.reason}_"
    )
    return {"messages": [handoff], "route": decision.agent}


# ---------------------------------------------------------------------------
# Specialists - one node per agent. Same LLM, different system prompt.
# Each is written out explicitly so you can read them top-to-bottom.
# ---------------------------------------------------------------------------

BUDGETING_PROMPT = """You are a warm, practical budgeting coach. You help people
build a spending plan, save for goals, set up an emergency fund, and pay down
debt. Talk in concrete numbers and habits, not theory.

Stay in your lane: if the user asks about picking investments or filing taxes,
give a one-line acknowledgement that another specialist handles that and offer
to continue with the budgeting angle. Never claim to be a CFP. Always remind
the user this is general guidance, not personal financial advice."""


def budgeting_node(state):
    messages = [SystemMessage(content=BUDGETING_PROMPT)] + state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}


INVESTING_PROMPT = """You are a clear-eyed investing educator. You explain index
funds, diversification, time horizon, dollar-cost averaging, and the role of
tax-advantaged accounts as *investment vehicles*. You don't pick individual
stocks or time the market.

Stay in your lane: if the user asks about budgeting habits or tax filing
mechanics, give a one-line acknowledgement that another specialist handles
that. Never claim to be a financial advisor. Always remind the user this is
educational content, not personal investment advice."""


def investing_node(state):
    messages = [SystemMessage(content=INVESTING_PROMPT)] + state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}


TAX_PROMPT = """You are a careful tax explainer. You cover deductions, credits,
filing basics, withholding, and the tax treatment of common accounts (401(k),
IRA, HSA). Always mention that rules vary by country and tax year, and that
specifics depend on the user's situation.

Stay in your lane: if the user asks how to budget or which fund to buy, give a
one-line acknowledgement that another specialist handles that. Never claim to
be a CPA or tax attorney. Always remind the user this is general information,
not legal or tax advice."""


def tax_node(state):
    messages = [SystemMessage(content=TAX_PROMPT)] + state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}


# ---------------------------------------------------------------------------
# Graph - supervisor -> conditional edge -> one specialist -> END.
# Every user turn starts fresh at the supervisor, so a topic pivot re-routes.
# ---------------------------------------------------------------------------


class State(TypedDict):
    messages: Annotated[list, add_messages]
    route: AgentName


def pick_specialist(state: State) -> AgentName:
    return state["route"]


builder = StateGraph(State)
builder.add_node("supervisor", supervisor_node)
builder.add_node("budgeting", budgeting_node)
builder.add_node("investing", investing_node)
builder.add_node("tax", tax_node)

builder.add_edge(START, "supervisor")
builder.add_conditional_edges(
    "supervisor",
    pick_specialist,
    {"budgeting": "budgeting", "investing": "investing", "tax": "tax"},
)
builder.add_edge("budgeting", END)
builder.add_edge("investing", END)
builder.add_edge("tax", END)

# This is what langgraph dev picks up from langgraph.json
graph = builder.compile()
