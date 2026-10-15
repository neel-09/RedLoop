import time
from redloop.sql_client import SQLClient

COLUMNS = ["ts", "run_id", "purpose", "family", "tier", "model_id", "prompt_tokens",
           "completion_tokens", "reasoning_tokens", "cost", "latency", "finish_reason",
           "cache_hit", "raw"]

SCHEMA = """CREATE TABLE IF NOT EXISTS calls (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts REAL, run_id TEXT, purpose TEXT, family TEXT, tier TEXT, model_id TEXT,
  prompt_tokens INTEGER, completion_tokens INTEGER, reasoning_tokens INTEGER,
  cost REAL, latency REAL, finish_reason TEXT, cache_hit INTEGER, raw TEXT)"""

GROUPABLE = {"tier", "purpose", "family", "run_id"}

class CallLog:
    def __init__(self, sql=None):
        self.sql = sql or SQLClient()
        self.sql.execute(SCHEMA)

    def record(self, **row):
        row.setdefault("ts", time.time())
        self.sql.execute(f"INSERT INTO calls ({','.join(COLUMNS)}) VALUES ({','.join('?' * len(COLUMNS))})",[row.get(c) for c in COLUMNS],)

    def total_cost(self, run_id=None):
        if run_id:
            q = "SELECT COALESCE(SUM(cost), 0) FROM calls WHERE run_id = ?"
            return self.sql.query(q, (run_id,))[0][0]
        return self.sql.query("SELECT COALESCE(SUM(cost), 0) FROM calls")[0][0]

    def cost_by(self, column):
        """Spend grouped by tier, purpose, family or run_id (for the dashboard and ledger)."""
        if column not in GROUPABLE:
            raise ValueError(f"cannot group by {column!r}; use one of {sorted(GROUPABLE)}")
        return self.sql.query(f"SELECT {column}, COUNT(*), SUM(cost) FROM calls GROUP BY {column}")
