# Sous Chef

A cooking assistant that demonstrates the **skills pattern with progressive
loading**. Instead of stuffing every domain prompt into one giant system
message, the agent keeps a tiny catalog at startup and loads expert
instructions on demand.

The agent runs as a LangGraph server locally and connects to
[agent-chat-ui](https://github.com/langchain-ai/agent-chat-ui) for the
frontend, the same way as the `agentchat` project.

## The pattern

Most agents look like this:

```
[System prompt: 4000 tokens of every rule about every skill]
[User message]
[Response]
```

Problem: even if the user just asks one question about wine pairings, the
agent paid for - and got distracted by - the rules for meal planning,
substitutions, knife technique, etc.

The skills pattern flips it:

```
[System prompt: tiny catalog of skill NAMES + one-line descriptions]
[User message]
  -> agent calls load_skill("pairing-expert")
[Tool returns: full pairing instructions]
[Response, now informed by the loaded skill]
```

The base context stays small. Only the skill the agent actually needs gets
loaded into the conversation. Adding a new skill is just a new markdown
file - no code changes.

This is the same pattern Claude Code uses for its own skill system.

## What's in the catalog

Five cooking skills, each a separate file in `skills/`:

| Skill | What it does |
|---|---|
| `recipe-finder` | Find recipes based on ingredients, cuisine, or dish name |
| `meal-planner` | Plan a week of meals with a unified shopping list |
| `technique-coach` | Teach knife cuts, searing, sauces, etc. with sensory cues |
| `substitutions` | Suggest ingredient swaps for diet, allergies, or pantry gaps |
| `pairing-expert` | Wine, beer, and non-alcoholic pairings for a dish |

Each is a markdown file with YAML frontmatter (`name`, `description`) and
a body of expert instructions.

## Getting started

### 1. Set up your environment

Copy the example env file and fill in your keys:

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

On startup you should see something like:

```
Loaded skill catalog: meal-planner, pairing-expert, recipe-finder, substitutions, technique-coach
- API: http://127.0.0.1:2024
- Studio UI: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
```

### 4. Start the chat UI

If you already have the `agent-chat-ui` set up from the `agentchat` project,
point it at this server:

- **Deployment URL**: `http://localhost:2024`
- **Assistant/Graph ID**: `agent`
- API key: leave blank

Otherwise, follow the agentchat README to install the UI once - both
projects share it.

## Things to try

Watch the tool calls in the LangGraph studio while you do these - you'll see
exactly which skill gets loaded for each question:

- "What can I make with chicken thighs and a sad-looking zucchini?"
  → loads `recipe-finder`
- "Plan me 4 weeknight dinners for 2 people, nothing too fancy."
  → loads `meal-planner`
- "I keep burning my onions. What am I doing wrong?"
  → loads `technique-coach`
- "I'm out of buttermilk. What can I use?"
  → loads `substitutions`
- "What should I drink with a mushroom risotto?"
  → loads `pairing-expert`
- "Plan me a dinner party - menu, technique tips for the trickiest dish, and
  wine pairings."
  → loads multiple skills, one at a time, as the agent works through it
- "Hey, what can you help with?"
  → answers directly from the catalog, no skill loaded

## Adding a new skill

1. Drop a new file in `skills/` named like `<slug>.md`.
2. Give it frontmatter:

   ```markdown
   ---
   name: my-new-skill
   description: One-line description the agent uses to decide when to load this
   ---

   # My New Skill

   Your detailed instructions go here...
   ```

3. Restart `langgraph dev`. That's it - no code changes.

The `description` is the only thing the agent sees up front, so write it
like a "when to use" hook, not a generic summary.

## Project structure

```
sous-chef/
  agent.py          # Tiny router agent + load_skill tool
  langgraph.json    # Tells langgraph dev where to find the graph
  requirements.txt  # Python dependencies
  .env.example      # Template for API keys
  skills/           # Drop new .md files here to extend the agent
    recipe-finder.md
    meal-planner.md
    technique-coach.md
    substitutions.md
    pairing-expert.md
```

## Why this is worth learning

- **Token economy.** Adding a 6th, 10th, 50th skill doesn't bloat every
  request. The base prompt grows by one line per skill, not one page.
- **Focus.** Each skill is written as if it's the only thing the agent does.
  No conditional logic like "if cooking, do X; if pairing, do Y."
- **Extensibility.** Non-engineers can add or edit skills - it's just
  markdown.
- **Debuggability.** When the agent gives a bad answer, you can read the
  exact instructions it was following.

## Troubleshooting

**"No skills found in .../skills"**
The agent expects at least one `.md` file in `skills/` with proper
frontmatter. Check the format matches the example above.

**"Skill X is missing YAML frontmatter"**
The file needs to start with `---`, a few `key: value` lines, then `---`,
then the body.

**Agent answers without loading any skill**
That's fine for chitchat or capability questions. If it's skipping a skill
that should clearly apply, tighten the `description` in the skill's
frontmatter so it reads more like "use this when ...".
