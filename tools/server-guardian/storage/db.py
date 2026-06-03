"""server-guardian/storage/db.py — SQLite 存储层

保存每次健康检查的快照数据，支持趋势查询和日报生成。
"""

import json
import os
import sqlite3
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

_LOCAL = threading.local()


class Storage:
    """健康检查数据存储。

    使用 SQLite 单文件存储，每行一条 JSON 记录 + 索引字段。
    线程安全（线程本地连接）。
    """

    def __init__(self, db_path: str):
        self._db_path = os.path.expanduser(db_path)
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)

    def _conn(self) -> sqlite3.Connection:
        """获取线程本地数据库连接。"""
        if not hasattr(_LOCAL, "conn") or _LOCAL.conn is None:
            conn = sqlite3.connect(self._db_path)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            self._init_tables(conn)
            _LOCAL.conn = conn
        return _LOCAL.conn

    def _init_tables(self, conn: sqlite3.Connection) -> None:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                hostname TEXT,
                snapshot_json TEXT NOT NULL,
                alert_count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_checks_ts
            ON checks(timestamp DESC)
        """)

    def close(self) -> None:
        if hasattr(_LOCAL, "conn") and _LOCAL.conn is not None:
            _LOCAL.conn.close()
            _LOCAL.conn = None

    def save_snapshot(self, snapshot: dict) -> int:
        """保存一次健康检查快照。

        Returns:
            插入的记录 ID。
        """
        conn = self._conn()
        alert_count = len(snapshot.get("alerts", []))
        conn.execute(
            "INSERT INTO checks (timestamp, hostname, snapshot_json, alert_count) "
            "VALUES (?, ?, ?, ?)",
            (
                snapshot.get("timestamp", ""),
                snapshot.get("hostname", ""),
                json.dumps(snapshot, ensure_ascii=False),
                alert_count,
            ),
        )
        conn.commit()
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    def get_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近 N 次检查记录。"""
        conn = self._conn()
        rows = conn.execute(
            "SELECT id, timestamp, hostname, snapshot_json, alert_count, created_at "
            "FROM checks ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()

        results = []
        for row in rows:
            try:
                snapshot = json.loads(row[3])
            except (json.JSONDecodeError, TypeError):
                snapshot = {}
            results.append({
                "id": row[0],
                "timestamp": row[1],
                "hostname": row[2],
                "snapshot": snapshot,
                "alert_count": row[4],
                "created_at": row[5],
            })
        results.reverse()  # 时间升序
        return results

    def get_today_snapshots(self) -> List[Dict[str, Any]]:
        """获取今天的所有检查记录。"""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        conn = self._conn()
        rows = conn.execute(
            "SELECT id, timestamp, hostname, snapshot_json, alert_count, created_at "
            "FROM checks WHERE timestamp >= ? ORDER BY id ASC",
            (today,),
        ).fetchall()

        results = []
        for row in rows:
            try:
                snapshot = json.loads(row[3])
            except (json.JSONDecodeError, TypeError):
                snapshot = {}
            results.append({
                "id": row[0],
                "timestamp": row[1],
                "hostname": row[2],
                "snapshot": snapshot,
                "alert_count": row[4],
            })
        return results

    def get_alert_history(self, days: int = 7) -> List[Dict[str, Any]]:
        """获取最近 N 天内有告警的记录。"""
        conn = self._conn()
        from datetime import timedelta
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        rows = conn.execute(
            "SELECT id, timestamp, hostname, snapshot_json, alert_count, created_at "
            "FROM checks WHERE timestamp >= ? AND alert_count > 0 "
            "ORDER BY id DESC",
            (since,),
        ).fetchall()

        results = []
        for row in rows:
            try:
                snapshot = json.loads(row[3])
            except (json.JSONDecodeError, TypeError):
                snapshot = {}
            results.append({
                "id": row[0],
                "timestamp": row[1],
                "alert_count": row[4],
                "alerts": snapshot.get("alerts", []),
            })
        return results

    def cleanup_old(self, days: int = 90) -> int:
        """清理超过 N 天的旧记录。"""
        conn = self._conn()
        from datetime import timedelta
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        deleted = conn.execute(
            "DELETE FROM checks WHERE timestamp < ?",
            (cutoff,),
        ).rowcount
        conn.commit()
        return deleted