import os
import json
from typing import Annotated, Sequence, TypedDict, Any, List, Optional, Dict
from dotenv import load_dotenv

import psycopg
from psycopg_pool import ConnectionPool
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

try:
    from langgraph.checkpoint.postgres import PostgresSaver
except ImportError:
    PostgresSaver = None

load_dotenv()

# System prompt enforcing health check -> runbook search -> resolution/escalation workflow
SYSTEM_PROMPT = (
    "You are an Autonomous Incident Triage Agent for cloud systems. "
    "Your objective is to investigate incidents, diagnose root causes, and propose remediation. "
    "MANDATORY WORKFLOW: "
    "1. Always check service health first using `query_service_health`. "
    "2. Next, search relevant remediation runbooks using `search_remediation_runbooks`. "
    "3. Analyze findings. If manual engineer intervention is required or service is severely degraded, "
    "call `escalate_ticket` to create an emergency ticket. Note that `escalate_ticket` requires human approval."
)

SERVICES_HEALTH_DB = {
    "auth": {
        "status": "DEGRADED",
        "error_rate": "8.5%",
        "latency_p99": "2400ms",
        "active_alerts": ["AuthServiceHigh504Rate", "RedisTokenCacheHighMemory"],
        "details": "High rate of HTTP 504 Gateway Timeouts on /auth/verify."
    },
    "database": {
        "status": "DEGRADED",
        "error_rate": "2.1%",
        "latency_p99": "1800ms",
        "active_alerts": ["PostgresConnectionPoolSaturation", "HighQueryLatency"],
        "details": "Connection pool usage at 96%, query queue latency elevated."
    },
    "payments": {
        "status": "UNHEALTHY",
        "error_rate": "14.2%",
        "latency_p99": "3100ms",
        "active_alerts": ["PaymentGateway502Spike", "CheckoutCircuitBreakerOpen"],
        "details": "Upstream payment provider returning 502 Bad Gateway."
    }
}

def extract_text(content: Any) -> str:
    """Normalize string, list of blocks, or dictionary structured content to plain text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                if "text" in item:
                    parts.append(item["text"])
                elif "content" in item:
                    parts.append(extract_text(item["content"]))
                else:
                    parts.append(json.dumps(item))
            else:
                parts.append(str(item))
        return "\n".join(parts)
    if isinstance(content, dict):
        if "text" in content:
            return content["text"]
        return json.dumps(content)
    return str(content)

@tool
def query_service_health(service: str) -> str:
    """Query real-time health metrics, error rates, latency, and active alerts for a service."""
    normalized = service.lower().strip()
    if normalized in SERVICES_HEALTH_DB:
        info = SERVICES_HEALTH_DB[normalized]
        return (
            f"Service '{normalized}' Status: {info['status']}\n"
            f"Error Rate: {info['error_rate']}, P99 Latency: {info['latency_p99']}\n"
            f"Active Alerts: {', '.join(info['active_alerts'])}\n"
            f"Details: {info['details']}"
        )
    return f"Service '{service}' status: HEALTHY (No active alerts or degradation found)."

def _fallback_runbook_search(query: str, service: Optional[str] = None) -> str:
    from seed_rag import RUNBOOKS
    matches = []
    query_terms = query.lower().split()
    for rb in RUNBOOKS:
        if service and rb["service"].lower() != service.lower():
            continue
        text = (rb["title"] + " " + rb["content"]).lower()
        score = sum(1 for term in query_terms if term in text)
        if score > 0 or not service or rb["service"].lower() == (service or "").lower():
            matches.append(rb)
    
    top_matches = matches[:2]
    if not top_matches:
        return "No relevant runbooks found."
    
    results = []
    for i, m in enumerate(top_matches, 1):
        results.append(f"[{i}] {m['title']} (Service: {m['service']}):\n{m['content']}")
    return "\n\n".join(results)

@tool
def search_remediation_runbooks(query: str, service: Optional[str] = None) -> str:
    """Search pgvector incident runbooks database for relevant remediation procedures."""
    db_url = os.getenv("DATABASE_URL")
    api_key = os.getenv("GEMINI_API_KEY")

    if not db_url or not api_key:
        return _fallback_runbook_search(query, service)

    try:
        embedding_model = os.getenv("GEMINI_EMBEDDING_MODEL", "models/text-embedding-004")
        embeddings = GoogleGenerativeAIEmbeddings(
            model=embedding_model,
            google_api_key=api_key,
            task_type="RETRIEVAL_QUERY"
        )
        query_vector = embeddings.embed_query(query)
        filter_json = json.dumps({"service": service.lower()}) if service else "{}"
        
        with psycopg.connect(db_url, prepare_threshold=None) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT title, service, content, similarity FROM match_incident_docs(%s, %s, %s);",
                    (f"[{','.join(map(str, query_vector))}]", 2, filter_json)
                )
                rows = cur.fetchall()
                if not rows:
                    return "No relevant runbooks found."
                results = []
                for i, r in enumerate(rows, 1):
                    results.append(f"[{i}] {r[0]} (Service: {r[1]}, Similarity: {r[3]:.2f}):\n{r[2]}")
                return "\n\n".join(results)
    except Exception:
        # Gracefully fall back to in-memory runbook search
        return _fallback_runbook_search(query, service)

@tool
def escalate_ticket(ticket_title: str, severity: str) -> str:
    """CRITICAL: Escalate incident to on-call engineering team and create high-priority paging ticket."""
    return f"Incident Ticket Created: '{ticket_title}' [Severity: {severity.upper()}]. On-call team paged successfully."

SAFE_TOOLS = [query_service_health, search_remediation_runbooks]
SENSITIVE_TOOL_NAMES = {"escalate_ticket"}
ALL_TOOLS = [query_service_health, search_remediation_runbooks, escalate_ticket]

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

def get_llm(model_override=None):
    if model_override:
        return model_override
    api_key = os.getenv("GEMINI_API_KEY") or "dummy-key"
    model_name = os.getenv("GEMINI_MODEL", "models/gemini-3.8-flash")
    return ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=api_key,
        temperature=0.0
    )

def create_agent_node(llm, tools):
    llm_with_tools = llm.bind_tools(tools)
    def agent_node(state: AgentState):
        messages = state["messages"]
        if not any(isinstance(m, SystemMessage) for m in messages):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}
    return agent_node

def route_tools(state: AgentState) -> str:
    """Harden routing: if ANY tool call is sensitive, route through the approval interrupt."""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        if any(tc.get("name") in SENSITIVE_TOOL_NAMES for tc in last_message.tool_calls):
            return "sensitive_tools"
        return "safe_tools"
    return END

def get_agent_app(llm_override=None, checkpointer=None, db_pool=None):
    llm = get_llm(llm_override)
    workflow = StateGraph(AgentState)
    
    workflow.add_node("agent", create_agent_node(llm, ALL_TOOLS))
    workflow.add_node("safe_tools", ToolNode(SAFE_TOOLS))
    # Sensitive node has access to ALL_TOOLS so mixed batches execute once approved
    workflow.add_node("sensitive_tools", ToolNode(ALL_TOOLS))
    
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", route_tools, {
        "safe_tools": "safe_tools",
        "sensitive_tools": "sensitive_tools",
        END: END
    })
    workflow.add_edge("safe_tools", "agent")
    workflow.add_edge("sensitive_tools", "agent")
    
    if checkpointer is not None:
        cp = checkpointer
    elif db_pool is not None and PostgresSaver is not None:
        cp = PostgresSaver(db_pool)
        cp.setup()
    elif os.getenv("DATABASE_URL") and PostgresSaver is not None:
        try:
            db_url = os.getenv("DATABASE_URL")
            # Quick connectivity test to avoid hanging the web UI on invalid credentials
            with psycopg.connect(db_url, connect_timeout=3, prepare_threshold=None) as test_conn:
                pass
            pool = ConnectionPool(
                db_url,
                max_size=10,
                kwargs={"autocommit": True, "prepare_threshold": None, "connect_timeout": 5}
            )
            cp = PostgresSaver(pool)
            cp.setup()
        except Exception as e:
            print(f"[Warning] Database connection unavailable ({e}). Running with in-memory checkpointer.")
            cp = MemorySaver()
    else:
        cp = MemorySaver()
        
    return workflow.compile(
        checkpointer=cp,
        interrupt_before=["sensitive_tools"]
    )

def approve_thread(app, thread_id: str):
    """Resume execution of an interrupted sensitive tool call."""
    config = {"configurable": {"thread_id": thread_id}}
    return app.invoke(None, config)

def reject_thread(app, thread_id: str, reason: str = "Rejected by on-call engineer."):
    """Reject pending sensitive tool calls by injecting ToolMessages for every pending call and resuming."""
    config = {"configurable": {"thread_id": thread_id}}
    state = app.get_state(config)
    if not state or not state.values.get("messages"):
        raise ValueError(f"No active state found for thread_id '{thread_id}'")
    
    last_message = state.values["messages"][-1]
    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
        raise ValueError(f"No pending tool calls found for thread_id '{thread_id}'")
    
    # Generate ToolMessage for EVERY pending tool call in the message
    tool_messages = [
        ToolMessage(
            content=f"Rejected by engineer: {reason}",
            tool_call_id=tc["id"]
        )
        for tc in last_message.tool_calls
    ]
    
    app.update_state(config, {"messages": tool_messages}, as_node="sensitive_tools")
    return app.invoke(None, config)
