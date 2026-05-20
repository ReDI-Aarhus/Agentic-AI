# Money Mentors

A personal-finance assistant that demonstrates **multi-agent routing**. Instead
of one agent with many tools (`agentchat`) or one agent that loads expert
instructions on demand (`sous-chef`), this app has three separate specialist
agents and a supervisor that picks one per turn.

The agent runs as a LangGraph server locally and connects to
[agent-chat-ui](https://github.com/langchain-ai/agent-chat-ui), same as the
other demos.

## The pattern

A typical "agent with tools" looks like this:

```
[User message] -> [One agent, many tools] -> [Response]
```

Multi-agent routing flips it: the supervisor picks a specialist, and that
specialist answers as if it were the only agent in the system.

```
[User message]
  -> [Supervisor classifies: budgeting / investing / tax]
  -> [One specialist answers with its own focused prompt]
  -> [Response]
```

The supervisor's decision is a typed Pydantic object (`{agent, reason}`), so
you can see exactly *why* a message got routed where it did - both in the
LangGraph studio and as an inline note in the chat.

Every user turn re-routes from scratch. If the conversation pivots from
budgeting to taxes, the supervisor visibly hands off to a different specialist
on the very next message.

## The team

| Specialist | What it does |
|---|---|
| `budgeting` | Spending plans, saving habits, emergency funds, debt payoff, cash flow |
| `investing` | Index funds, asset allocation, time horizon, retirement accounts as investments |
| `tax` | Deductions, credits, filing basics, withholding, tax-advantaged accounts as shelters |

Each specialist has its own system prompt, stays in its lane, and reminds you
that this is educational - not personal financial advice.

## Getting started

### 1. Set up your environment

```bash
cp .env.example .env
```

You need:
- `OPENAI_ENDPOINT` - base URL for the LLM (the class proxy / Azure endpoint)
- `OPENAI_API_KEY` - API key for that endpoint
- `LANGSMITH_API_KEY` - for the LangGraph server (free at
  [smith.langchain.com](https://smith.langchain.com/settings))

### 2. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The LangGraph CLI is included in `requirements.txt`, so no separate install is needed.

### 3. Start the agent server

```bash
langgraph dev
```

On startup you should see:

```
- API: http://127.0.0.1:2024
- Studio UI: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
```

### 4. Start the chat UI

If you already have `agent-chat-ui` set up from the `agentchat` project, point
it at this server:

- **Deployment URL**: `http://localhost:2024`
- **Assistant/Graph ID**: `agent`
- API key: leave blank

## Things to try

Open the LangGraph studio in one tab and the chat UI in another. Watch the
supervisor node fire on every turn and pick a different specialist as the
conversation moves.

- "How do I build a $5k emergency fund on a $3,500/month take-home?"
  → routes to `budgeting`
- "Should I dollar-cost-average into a total-market index fund?"
  → routes to `investing`
- "Can I deduct my home office in 2026?"
  → routes to `tax`
- "I just got a $10k raise. What should I do with it?"
  → ambiguous on purpose - watch which specialist the supervisor picks and read
    the `reason` field in the trace
- After any of the above, follow up with: "And what are the tax implications?"
  → supervisor re-routes to `tax` on the next turn, even mid-conversation

## Project structure

```
money-mentors/
  agent.py          # Supervisor + three specialists + routing graph
  langgraph.json    # Tells langgraph dev where to find the graph
  requirements.txt  # Python dependencies
  .env.example      # Template for API keys
```

## Why this is worth learning

- **Separation of concerns.** Each specialist is written as if it's the only
  agent. No "if budgeting do X else if investing do Y" branching in prompts.
- **Visible decisions.** Structured output makes the routing decision a typed
  object, not a guess. Great for debugging, evals, and lecturing.
- **Easy to extend.** Add a fourth specialist by writing one prompt and adding
  one node + one edge to the graph.

## Extensions to try

Once the basic demo makes sense, try one of these as an exercise:

1. **Sticky specialists.** Add a `current_agent` field to state. Re-route only
   when the supervisor explicitly decides the topic has changed.
2. **Per-specialist tools.** Give the investing agent a tool that fetches
   index-fund expense ratios, and the tax agent a tool that looks up the
   current standard deduction. Now each specialist is a real ReAct loop.
3. **A fourth specialist.** Add `insurance` or `estate` and watch how the
   supervisor's routing accuracy holds up.
4. **Confidence threshold.** Have the supervisor emit a confidence score; if
   it's low, ask the user a clarifying question instead of routing.

## Troubleshooting

**Supervisor always routes to the same specialist**
Check the catalog in `SUPERVISOR_PROMPT` in `agent.py` - the descriptions are
how the supervisor decides. Tighten them so each one reads like a clear "use
this when..." hook.

**The chat UI doesn't show the "Routing to..." line**
That message is added by `supervisor_node` in `agent.py`. If you removed it,
restore it - or check the LangGraph studio, where the decision appears in the
supervisor node's output regardless.

**Specialists answer outside their lane**
Their system prompts include a "stay in your lane" rule. If a specialist
ignores it, tighten that part of its prompt or add a few-shot example.
