import sqlite3
from pathlib import Path

class SQLClient:
    def __init__(self, path="data/redloop.db"):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)

    def execute(self, sql, params=()):
        cur = self.db.execute(sql, params)
        self.db.commit()
        return cur

    def query(self, sql, params=()):
        return self.db.execute(sql, params).fetchall()