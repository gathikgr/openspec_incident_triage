import os
import json
from dotenv import load_dotenv
import psycopg
from langchain_google_genai import GoogleGenerativeAIEmbeddings

load_dotenv()

RUNBOOKS = [
    {
        "title": "Auth Service 504 Timeouts and Token Latency",
        "service": "auth",
        "content": (
            "Symptoms: High rate of HTTP 504 Gateway Timeouts on /auth/verify and /oauth/token endpoints. "
            "Root causes: Redis token cache exhaustion, stale session locks, or OAuth provider throttling. "
            "Remediation Steps: 1. Check Redis memory and connection saturation. 2. Restart auth worker pods. "
            "3. If latency persists above 2000ms, scale auth replicas by 50% and flush expired session cache. "
            "4. If upstream provider is down, trigger ticket escalation to on-call security engineer."
        ),
        "metadata": {"service": "auth", "tier": 1, "category": "authentication"}
    },
    {
        "title": "Database High Latency and Connection Pool Saturation",
        "service": "database",
        "content": (
            "Symptoms: Database query latency exceeds 500ms, transaction pooler queues queries, client timeouts. "
            "Root causes: Long-running unindexed analytical query, locked rows during migration, or pool exhaustion. "
            "Remediation Steps: 1. Run pg_stat_activity to identify active queries running > 30s. "
            "2. Terminate blocking backend PID using pg_cancel_backend() or pg_terminate_backend(). "
            "3. Verify connection pooler connection limits and recycle idle connections. "
            "4. If storage IOPS are maxed out, escalate to DBA on-call for instance vertical scaling."
        ),
        "metadata": {"service": "database", "tier": 1, "category": "storage"}
    },
    {
        "title": "Payment Gateway 502 Failures and Transaction Errors",
        "service": "payments",
        "content": (
            "Symptoms: Checkout failures with HTTP 502/503 from payment service, dropped webhooks. "
            "Root causes: Primary payment processor outage, webhook receiver signature mismatch, or rate limiting. "
            "Remediation Steps: 1. Inspect payment gateway health dashboard and error codes. "
            "2. Enable secondary payment gateway fallback routing in payment service config. "
            "3. Verify webhook retry queue is active and buffer outgoing payment notifications. "
            "4. If financial settlement or reconciliation errors occur, escalate immediately to Payments Lead."
        ),
        "metadata": {"service": "payments", "tier": 1, "category": "billing"}
    }
]

def get_embeddings_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is required.")
    return GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004",
        google_api_key=api_key,
        task_type="RETRIEVAL_DOCUMENT"
    )

def seed_runbooks(database_url: str = None, embeddings_client = None):
    db_url = database_url or os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable is required.")
    
    client = embeddings_client or get_embeddings_client()
    
    # Generate embeddings for each runbook
    contents = [r["content"] for r in RUNBOOKS]
    embeddings = client.embed_documents(contents)
    
    with psycopg.connect(db_url, prepare_threshold=None, autocommit=True) as conn:
        with conn.cursor() as cur:
            for runbook, embedding in zip(RUNBOOKS, embeddings):
                embedding_str = f"[{','.join(map(str, embedding))}]"
                cur.execute(
                    """
                    INSERT INTO incident_docs (title, service, content, metadata, embedding)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (service, title) 
                    DO UPDATE SET 
                        content = EXCLUDED.content,
                        metadata = EXCLUDED.metadata,
                        embedding = EXCLUDED.embedding;
                    """,
                    (
                        runbook["title"],
                        runbook["service"],
                        runbook["content"],
                        json.dumps(runbook["metadata"]),
                        embedding_str
                    )
                )
    print(f"Successfully seeded {len(RUNBOOKS)} incident runbooks.")

if __name__ == "__main__":
    seed_runbooks()
