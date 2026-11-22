import os
import sqlite3
from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from config import (
    CHAT_DB_PATH,
    CONTEXT_WINDOW_MESSAGES,
    FALLBACK_GEMINI_MODEL,
    FALLBACK_GROQ_MODELS,
    MAX_OUTPUT_TOKENS,
    PRIMARY_GROQ_MODEL,
    SYSTEM_PROMPT,
    TEMPERATURE,
)

load_dotenv()


# 1. Shared Graph State
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


# 2. Fast Primary LLM + Automatic Free-Tier Fallbacks
primary_llm = ChatGroq(
    model=PRIMARY_GROQ_MODEL,
    temperature=TEMPERATURE,
    max_tokens=MAX_OUTPUT_TOKENS,
    reasoning_effort="low",
)

fallback_llms = [
    ChatGroq(
        model=model_name,
        temperature=TEMPERATURE,
        max_tokens=MAX_OUTPUT_TOKENS,
        reasoning_effort="low",
    )
    for model_name in FALLBACK_GROQ_MODELS
] + [
    ChatGoogleGenerativeAI(
        model=FALLBACK_GEMINI_MODEL,
        temperature=TEMPERATURE,
        max_output_tokens=MAX_OUTPUT_TOKENS,
        reasoning_effort="low",
    )
]

llm = primary_llm.with_fallbacks(fallback_llms)


# 3. Single Chat Node (uses sliding window to save tokens while SQLite keeps full history)
def chat_node(state: ChatState):
    recent_messages = state["messages"][-CONTEXT_WINDOW_MESSAGES:]
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + recent_messages
    response = llm.invoke(messages)
    return {"messages": [response]}


# 4. Compile Graph with SQLite Persistence
os.makedirs(os.path.dirname(CHAT_DB_PATH), exist_ok=True)
conn = sqlite3.connect(CHAT_DB_PATH, check_same_thread=False)
checkpointer = SqliteSaver(conn=conn)
checkpointer.setup()  # Creates checkpoints tables automatically on first run

graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)

chatbot = graph.compile(checkpointer=checkpointer)


# 5. Thread Helpers
def get_all_threads() -> list[str]:
    """Return all unique thread IDs saved in SQLite (newest first)."""
    threads = []
    for checkpoint in checkpointer.list(None):
        tid = checkpoint.config["configurable"]["thread_id"]
        if tid not in threads:
            threads.append(tid)
    return threads


def get_thread_title(thread_id: str) -> str:
    """Display the first user message as the sidebar thread title."""
    state = chatbot.get_state(config={"configurable": {"thread_id": thread_id}})
    messages = state.values.get("messages", [])
    for msg in messages:
        if isinstance(msg, HumanMessage) and msg.content:
            text = str(msg.content).strip()
            return text[:32] + ("..." if len(text) > 32 else "")
    return f"New Chat ({thread_id[:6]})"