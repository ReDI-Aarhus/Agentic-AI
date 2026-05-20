# Agent Chat

A research assistant with RAG (Vestas Annual Report) and Wikipedia search, served through a web chat interface.

The agent runs as a LangGraph server locally and connects to [agent-chat-ui](https://github.com/langchain-ai/agent-chat-ui) for the frontend. Streaming works out of the box - you get token-by-token output in the chat, including when the agent is retrieving documents or searching Wikipedia.

## What it does

- Answers questions about Vestas using RAG over their 2024 annual report
- Answers general knowledge questions using Wikipedia
- Decides which source to use based on the question
- Streams responses in real time through the chat UI

## Getting started

### 1. Copy the data

The agent needs the Vestas PDF from the RAG exercises. Copy it into a `data/` folder here:

```bash
mkdir -p data
cp ../../exercises/8-rag/exercises/data/"Vestas Annual Report 2024.pdf" data/
```

### 2. Set up your environment

Copy the example env file and fill in your API keys:

```bash
cp .env.example .env
```

You need:
- `AZURE_OPENAI_API_KEY` - for the Azure-hosted embeddings (`text-embedding-3-large`)
- `OPENAI_ENDPOINT` - base URL for the LLM (proxied through Azure)
- `OPENAI_API_KEY` - API key for the LLM endpoint
- `LANGSMITH_API_KEY` - for the LangGraph server (free at [smith.langchain.com](https://smith.langchain.com/settings))

You also need to paste your Azure endpoint into `agent.py` where `azure_endpoint=""` is set on `AzureOpenAIEmbeddings`.

### 3. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The LangGraph CLI is included in `requirements.txt`, so no separate install is needed.

### 4. Start the agent server

```bash
langgraph dev
```

This starts the server at `http://localhost:2024`. On first run it loads and embeds the PDF, which takes about a minute. After that you should see:

```
- API: http://127.0.0.1:2024
- Studio UI: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
```

### 5. Start the chat UI

The chat UI is already included in the `agent-chat-ui/` folder with dependencies installed. In a separate terminal:

```bash
cd agent-chat-ui
pnpm dev
```

Open `http://localhost:3000` in your browser. When it asks for configuration:
- **Deployment URL**: `http://localhost:2024`
- **Assistant/Graph ID**: `agent`
- Leave the API key blank (not needed for local dev)

You need Node.js installed. If `pnpm` isn't available: `npm install -g pnpm`.

## Things to try

- "What was Vestas' revenue in 2024?"
- "How many wind turbines did Vestas install last year?"
- "What is the history of wind energy?" (this one hits Wikipedia)
- "Compare Vestas' sustainability goals with general industry trends" (uses both sources)

## Project structure

```
agentchat/
  agent.py          # The agent graph - RAG setup, tools, LLM, routing
  langgraph.json    # Tells langgraph dev where to find the graph
  requirements.txt  # Python dependencies
  .env.example      # Template for API keys
  data/             # Put the Vestas PDF here
  agent-chat-ui/    # The chat frontend (pre-installed)
```

## Troubleshooting

**"FileNotFoundError: Could not find Vestas Annual Report 2024.pdf"**
You need to copy the PDF into the `data/` folder. See step 1 above.

**Server starts but the chat UI can't connect**
Make sure the deployment URL is `http://localhost:2024` (not https). If you're on Safari, try Chrome or run `langgraph dev --tunnel`.

**Embedding takes forever**
The PDF is about 220 pages and creates ~1100 chunks. First run takes a minute or so. This is normal - it re-embeds on every restart because we use an in-memory vector store.
