import sqlite3
import httpx
from datetime import datetime

DB_PATH = 'aira_memory.db'
OLLAMA_URL = 'http://localhost:11434/api/generate'
COMPRESSION_THRESHOLD = 20
SUMMARY_CHUNK_SIZE = 10
RECENT_SUMMARIES_TO_INJECT = 3

class MemoryManager:
    def __init__(self):
        self.init_db()
        self.active_context: list[dict] = []
        self.chroma_client = None  # Phase 3 stub

    def init_db(self):
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS session_summaries (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    summary   TEXT NOT NULL
                )
            ''')
            conn.commit()

    # ── Tier 1 ──────────────────────────────────────────────
    async def add_message(self, role: str, content: str):
        self.active_context.append({'role': role, 'content': content})
        if len(self.active_context) >= COMPRESSION_THRESHOLD:
            await self._compress_to_tier2()

    # ── Tier 2 ──────────────────────────────────────────────
    async def _compress_to_tier2(self):
        chunk = self.active_context[:SUMMARY_CHUNK_SIZE]
        self.active_context = self.active_context[SUMMARY_CHUNK_SIZE:]
        conv = '\n'.join([f"{m['role'].upper()}: {m['content']}" for m in chunk])
        prompt = (
            'Summarize this interaction between Harris and AIRA into exactly '
            '3 sentences. Capture: (1) core topics, (2) decisions/facts, '
            '(3) emotional tone. Be specific.\n\n' + conv
        )
        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(OLLAMA_URL, json={
                    'model': 'gemma4', 'prompt': prompt, 'stream': False,
                    'options': {'num_ctx': 4096, 'temperature': 0.3}
                }, timeout=30.0)
                r.raise_for_status()
                summary = r.json().get('response', '').strip()
        except Exception as e:
            summary = f'Compression error at {datetime.now().isoformat()}: {e}'
        self._save_summary(summary)
        await self._embed_to_tier3(summary)  # Phase 3 hook
        print(f'[MemoryManager] Compressed → {summary[:60]}...')

    def _save_summary(self, summary: str):
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                'INSERT INTO session_summaries (timestamp, summary) VALUES (?, ?)',
                (datetime.now().isoformat(), summary)
            )
            conn.commit()

    def get_recent_summaries(self, limit=RECENT_SUMMARIES_TO_INJECT) -> str:
        with sqlite3.connect(DB_PATH) as conn:
            rows = conn.execute(
                'SELECT timestamp, summary FROM session_summaries'
                ' ORDER BY id DESC LIMIT ?', (limit,)
            ).fetchall()
        if not rows: return ''
        lines = ['[AIRA Long-Term Memory — Recent Context]']
        for ts, s in reversed(rows):
            lines.append(f'• ({ts[:10]}) {s}')
        return '\n'.join(lines)

    # ── Tier 3 Stub (Phase 3) ────────────────────────────────
    async def _embed_to_tier3(self, text: str):
        if self.chroma_client is None: return
        # TODO Phase 3:
        # collection = self.chroma_client.get_or_create_collection('aira_memory')
        # collection.add(documents=[text], ids=[str(datetime.now().timestamp())])

    async def semantic_search(self, query: str, n_results=3) -> str:
        if self.chroma_client is None:
            return self.get_recent_summaries()  # graceful fallback
        # TODO Phase 3: return chroma similarity search results

    # ── Prompt Builder ───────────────────────────────────────
    def build_prompt(self, system_instruction: str) -> str:
        # NOTE: active_context already contains the new user message.
        # Do NOT pass user_input here — causes double injection.
        recent_memory = self.get_recent_summaries()
        active = '\n'.join(
            [f"{m['role'].upper()}: {m['content']}" for m in self.active_context]
        )
        parts = [system_instruction]
        if recent_memory: parts.append(recent_memory)
        if active: parts.append(active)
        parts.append('AIRA:')
        return '\n\n'.join(parts)
