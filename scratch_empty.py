import json
import sqlite3

db = sqlite3.connect("data/redloop.db")
rows = db.execute(
    "SELECT id, finish_reason, completion_tokens, raw FROM calls "
    "WHERE run_id LIKE 'benign-tool_assistant-%' ORDER BY id"
).fetchall()
for i, fr, ct, raw in rows:
    m = json.loads(raw)["choices"][0]["message"]
    if not (m.get("content") or "").strip() and not m.get("tool_calls"):
        reasoning = m.get("reasoning") or m.get("reasoning_content") or ""
        print(i, fr, ct, "reasoning:", repr(reasoning[:300]))
