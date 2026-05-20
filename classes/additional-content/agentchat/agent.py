"""
A simple agent with RAG and Wikipedia tools, built for use with langgraph dev
and the agent-chat-ui frontend.
"""

import os
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.retrievers import WikipediaRetriever
from langchain_core.messages import SystemMessage
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import ChatOpenAI, AzureOpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.tools.retriever import create_retriever_tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict

load_dotenv()

# ---------------------------------------------------------------------------
# RAG setup - load the Vestas annual report and build a vector index.
# This runs on every startup. It takes a moment, but keeps things simple.
# ---------------------------------------------------------------------------

DATA_DIR = Path(__file__).parent / "data"
VESTAS_PDF = DATA_DIR / "Vestas Annual Report 2024.pdf"

if not VESTAS_PDF.exists():
    raise FileNotFoundError(
        f"Could not find {VESTAS_PDF}. "
        "Copy the PDF from exercises/8-rag/exercises/data/ into the data/ folder. "
        "Check the README for details."
    )

print(f"Loading {VESTAS_PDF.name}...")
loader = PyPDFLoader(str(VESTAS_PDF))
pages = loader.load()

splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = splitter.split_documents(pages)
print(f"Split into {len(chunks)} chunks. Embedding...")

embeddings = AzureOpenAIEmbeddings(
    model="text-embedding-3-large",
    azure_endpoint="",  # TODO: paste your Azure endpoint here
)
vector_store = InMemoryVectorStore(embeddings)
vector_store.add_documents(chunks)
print("Vector store ready.")

# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

# RAG tool - searches the Vestas annual report
rag_retriever = vector_store.as_retriever(search_kwargs={"k": 4})
vestas_tool = create_retriever_tool(
    rag_retriever,
    "search_vestas_report",
    "Search the Vestas Annual Report 2024. Use this for questions about Vestas, "
    "wind turbines, their financials, sustainability targets, or anything related "
    "to the company.",
)

# Wikipedia tool - general knowledge lookup
wiki_retriever = WikipediaRetriever(top_k_results=2)
wiki_tool = create_retriever_tool(
    wiki_retriever,
    "search_wikipedia",
    "Search Wikipedia for general knowledge. Good for background info, "
    "definitions, historical facts, or anything not in the Vestas report.",
)

tools = [vestas_tool, wiki_tool]

# ---------------------------------------------------------------------------
# The LLM
# ---------------------------------------------------------------------------

llm = ChatOpenAI(
    base_url=os.environ["OPENAI_ENDPOINT"],
    model="gpt-5.4-mini",
    temperature=0,
)
llm_with_tools = llm.bind_tools(tools)

# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are a helpful research assistant. You have access to two sources:\n"
    "1. The Vestas Annual Report 2024 (use search_vestas_report)\n"
    "2. Wikipedia (use search_wikipedia)\n\n"
    "When answering questions about Vestas or wind energy, always search the report first. "
    "For general knowledge questions, use Wikipedia. "
    "Cite which source you used in your answer."
)


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
