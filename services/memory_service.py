import sqlite3
import httpx
from datetime import datetime
from core.config import DB_PATH, GROQ_MODEL, GROQ_API_KEY, OLLAMA_URL
from core.chroma import get_chroma_collection
from groq import Groq
import os

os.makedirs("data", exist_ok=True)

client = Groq(api_key=GROQ_API_KEY)

COMPRESSION_THRESHOLD = 20
SUMMARY_CHUNK_SIZE = 10
RECENT_SUMMARIES_LIMIT = 3
TIER3_SEARCH_RESULTS = 2
EMBED_MODEL = "nomic-embed-text"


async def _get_embedding(text: str) -> list[float]:
    async with httpx.AsyncClient() as http:
        response = await http.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": text},
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()["embedding"]


class MemoryManager:
    def __init__(self):
        self.active_context: list[dict] = []
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS session_summaries (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    summary   TEXT NOT NULL
                )
            ''')
            conn.commit()

    # ── Tier 1 ──────────────────────────────────────
    async def add_message(self, role: str, content: str):
        self.active_context.append({"role": role, "content": content})
        if len(self.active_context) >= COMPRESSION_THRESHOLD:
            await self._compress_to_tier2()

    # ── Tier 2 ──────────────────────────────────────
    async def _compress_to_tier2(self):
        chunk = self.active_context[:SUMMARY_CHUNK_SIZE]
        self.active_context = self.active_context[SUMMARY_CHUNK_SIZE:]
        conv = "\n".join([
            f"{'Harris' if m['role'] == 'user' else 'AIRA'}: {m['content']}"
            for m in chunk
        ])
        prompt = (
            "Summarize this conversation between Harris and AIRA in exactly 3 sentences. "
            "Capture: (1) core topics, (2) decisions or facts, (3) emotional tone. "
            "Be specific and concise.\n\n" + conv
        )
        try:
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=256,
            )
            summary = response.choices[0].message.content.strip()
        except Exception as e:
            summary = f"[Compression error at {datetime.now().isoformat()}: {e}]"

        self._save_summary(summary)
        await self._store_to_tier3(summary)
        print(f"[Memory] Compressed → {summary[:60]}...")

    def _save_summary(self, summary: str):
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                "INSERT INTO session_summaries (timestamp, summary) VALUES (?, ?)",
                (datetime.now().isoformat(), summary)
            )
            conn.commit()

    # ── Tier 3 ──────────────────────────────────────
    async def _store_to_tier3(self, summary: str):
        try:
            embedding = await _get_embedding(summary)
            collection = get_chroma_collection()
            doc_id = f"summary_{datetime.now().timestamp()}"
            collection.add(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[summary],
                metadatas=[{"timestamp": datetime.now().isoformat()}]
            )
            print(f"[Memory] Tier 3 stored → {doc_id}")
        except Exception as e:
            print(f"[Memory] Tier 3 store failed: {e}")

    async def search_tier3(self, query: str, n_results=TIER3_SEARCH_RESULTS) -> str:
        try:
            collection = get_chroma_collection()
            if collection.count() == 0:
                return ""
            embedding = await _get_embedding(query)
            results = collection.query(
                query_embeddings=[embedding],
                n_results=min(n_results, collection.count())
            )
            docs = results.get("documents", [[]])[0]
            if not docs:
                return ""
            lines = ["[AIRA Long-Term Memory]"]
            for doc in docs:
                lines.append(f"• {doc}")
            return "\n".join(lines)
        except Exception as e:
            print(f"[Memory] Tier 3 search failed: {e}")
            return ""

    # ── Context for Groq ────────────────────────────
    def get_recent_summaries(self, limit=RECENT_SUMMARIES_LIMIT) -> str:
        with sqlite3.connect(DB_PATH) as conn:
            rows = conn.execute(
                "SELECT timestamp, summary FROM session_summaries"
                " ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        if not rows:
            return ""
        lines = ["[AIRA Memory — Recent Context]"]
        for ts, s in reversed(rows):
            lines.append(f"• ({ts[:10]}) {s}")
        return "\n".join(lines)

    def get_messages_for_groq(self) -> list[dict]:
        return [
            {"role": "user" if m["role"] == "user" else "assistant",
             "content": m["content"]}
            for m in self.active_context
        ]

    def get_summary_count(self) -> int:
        with sqlite3.connect(DB_PATH) as conn:
            return conn.execute(
                "SELECT COUNT(*) FROM session_summaries"
            ).fetchone()[0]

    def get_tier3_count(self) -> int:
        try:
            return get_chroma_collection().count()
        except:
            return 0

    def clear_context(self):
        self.active_context = []

    def clear_all(self):
        self.active_context = []
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("DELETE FROM session_summaries")
            conn.commit()
        try:
            collection = get_chroma_collection()
            collection.delete(where={"timestamp": {"$gte": "0"}})
        except Exception as e:
            print(f"[Memory] Tier 3 clear failed: {e}")