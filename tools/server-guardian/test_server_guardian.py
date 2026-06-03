#!/usr/bin/env python3
"""test_server_guardian.py — server-guardian 单元测试

测试核心模块（不依赖外部服务）。
"""

import os
import sys
import json
import unittest
import tempfile
import shutil

# 确保项目根目录可导入
_project_root = os.path.dirname(os.path.abspath(__file__))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from core import checkers
from core import evaluator
from core import collector
from storage.db import Storage


# ── Checkers Tests ──────────────────────────────────────────

class TestCheckersCPU(unittest.TestCase):
    def test_collect_cpu_returns_dict(self):
        result = checkers.collect_cpu()
        self.assertIsInstance(result, (dict, type(None)))

    def test_cpu_keys(self):
        result = checkers.collect_cpu()
        if result:
            self.assertIn("percent", result)
            self.assertIn("cores", result)

    def test_cpu_values_range(self):
        result = checkers.collect_cpu()
        if result:
            self.assertGreaterEqual(result["percent"], 0.0)
            self.assertLessEqual(result["percent"], 100.0)
            self.assertGreater(result["cores"], 0)


class TestCheckersMemory(unittest.TestCase):
    def test_collect_memory_returns_dict(self):
        result = checkers.collect_memory()
        self.assertIsInstance(result, (dict, type(None)))

    def test_memory_keys(self):
        result = checkers.collect_memory()
        if result:
            for key in ("total_gb", "used_gb", "percent"):
                self.assertIn(key, result)

    def test_memory_values_positive(self):
        result = checkers.collect_memory()
        if result:
            self.assertGreater(result["total_gb"], 0)
            self.assertGreater(result["used_gb"], 0)


class TestCheckersDisk(unittest.TestCase):
    def test_returns_list(self):
        result = checkers.collect_disk()
        self.assertIsInstance(result, list)

    def test_contains_root(self):
        result = checkers.collect_disk()
        mounts = [e["mount"] for e in result]
        self.assertIn("/", mounts)

    def test_entry_format(self):
        result = checkers.collect_disk()
        for entry in result:
            self.assertIn("mount", entry)
            self.assertIn("total_gb", entry)
            self.assertIn("used_gb", entry)
            self.assertIn("percent", entry)

    def test_percent_in_range(self):
        result = checkers.collect_disk()
        for entry in result:
            self.assertGreaterEqual(entry["percent"], 0.0)
            self.assertLessEqual(entry["percent"], 100.0)


class TestCheckersSwap(unittest.TestCase):
    def test_returns_dict(self):
        result = checkers.collect_swap()
        self.assertIsInstance(result, dict)
        self.assertIn("total_gb", result)
        self.assertIn("used_gb", result)
        self.assertIn("percent", result)


class TestCheckersLoad(unittest.TestCase):
    def test_returns_dict(self):
        result = checkers.collect_load_avg()
        self.assertIsInstance(result, (dict, type(None)))

    def test_has_keys(self):
        result = checkers.collect_load_avg()
        if result:
            for key in ("1min", "5min", "15min"):
                self.assertIn(key, result)


class TestCheckersProcess(unittest.TestCase):
    def test_find_existing_process(self):
        count = checkers.find_process("python3")
        self.assertGreaterEqual(count, 0)

    def test_find_nonexistent(self):
        count = checkers.find_process("__definitely_not_running_xyz__")
        self.assertEqual(count, 0)


class TestCheckersPort(unittest.TestCase):
    def test_known_open_port(self):
        result = checkers.check_port(22)
        self.assertIsInstance(result, bool)

    def test_random_high_port(self):
        result = checkers.check_port(65530)
        self.assertFalse(result)


class TestCheckersSQLite(unittest.TestCase):
    def test_integrity_on_invalid_path(self):
        result = checkers.check_sqlite_integrity("/nonexistent/db.sqlite")
        self.assertEqual(result, "not_found")

    def test_integrity_on_valid_db(self):
        # 创建临时 SQLite 数据库
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            import sqlite3
            conn = sqlite3.connect(db_path)
            conn.execute("CREATE TABLE test (id INTEGER)")
            conn.execute("INSERT INTO test VALUES (1)")
            conn.commit()
            conn.close()

            result = checkers.check_sqlite_integrity(db_path)
            self.assertEqual(result, "ok")
        finally:
            os.unlink(db_path)


# ── Evaluator Tests ─────────────────────────────────────────

class TestEvaluator(unittest.TestCase):
    def setUp(self):
        self.config = {
            "thresholds": {
                "memory": {"warning": 80, "critical": 92},
                "disk": {"warning": 80, "critical": 90},
                "swap": {"warning": 50, "critical": 75},
                "cpu": {"warning": 80, "critical": 95},
                "load": {"warning": 4.0, "critical": 8.0},
                "process_count": {"warning": 200},
            }
        }

    def test_no_alerts_on_normal_snapshot(self):
        snapshot = {
            "system": {
                "memory": {"percent": 50},
                "swap": {"percent": 10},
                "cpu": {"percent": 20},
                "disk": [{"mount": "/", "percent": 60}],
                "load_avg": {"1min": 0.5},
                "process_count": 100,
            },
            "processes": [
                {"name": "nginx", "status": "ok", "port_open": True},
            ],
            "ports": [{"port": 22, "open": True}],
            "paths": [],
            "kanban": {"status": "ok"},
        }
        alerts = evaluator.evaluate(snapshot, self.config)
        self.assertEqual(len(alerts), 0)

    def test_critical_memory_alert(self):
        snapshot = {
            "system": {"memory": {"percent": 95}},
            "processes": [], "ports": [], "paths": [], "kanban": {},
        }
        alerts = evaluator.evaluate(snapshot, self.config)
        self.assertTrue(any(a["level"] == "critical" for a in alerts))

    def test_warning_memory_alert(self):
        snapshot = {
            "system": {"memory": {"percent": 85}},
            "processes": [], "ports": [], "paths": [], "kanban": {},
        }
        alerts = evaluator.evaluate(snapshot, self.config)
        self.assertTrue(any(a["level"] == "warning" for a in alerts))

    def test_disk_critical_alert(self):
        snapshot = {
            "system": {"disk": [{"mount": "/", "percent": 95}]},
            "processes": [], "ports": [], "paths": [], "kanban": {},
        }
        alerts = evaluator.evaluate(snapshot, self.config)
        self.assertTrue(any(a["level"] == "critical" for a in alerts))

    def test_process_down_is_critical(self):
        snapshot = {
            "processes": [{"name": "hermes", "status": "down"}],
            "system": {}, "ports": [], "paths": [], "kanban": {},
        }
        alerts = evaluator.evaluate(snapshot, self.config)
        self.assertTrue(any(a["module"] == "process:hermes" for a in alerts))

    def test_uptime_info_when_old(self):
        snapshot = {
            "uptime_seconds": 65 * 86400,  # 65 days
            "system": {}, "processes": [], "ports": [], "paths": [], "kanban": {},
        }
        # 确保 uptime_days 阈值在配置中
        config = dict(self.config)
        config["thresholds"]["uptime_days"] = {"warning": 60}
        alerts = evaluator.evaluate(snapshot, config)
        self.assertTrue(any(a["module"] == "uptime" for a in alerts))

    def test_alerts_sorted_by_severity(self):
        snapshot = {
            "system": {
                "memory": {"percent": 95},
                "disk": [{"mount": "/", "percent": 91}],
                "cpu": {"percent": 50},
                "load_avg": {"1min": 0.5},
                "swap": {"percent": 50},
                "process_count": 100,
            },
            "processes": [
                {"name": "nginx", "status": "down"},
            ],
            "ports": [],
            "paths": [],
            "kanban": {"status": "ok"},
        }
        alerts = evaluator.evaluate(snapshot, self.config)
        levels = [a["level"] for a in alerts]
        expected_order = ["critical", "critical", "critical"]
        self.assertEqual(levels[:3], expected_order)


# ── Storage Tests ───────────────────────────────────────────

class TestStorage(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmpdir, "test.db")
        self.storage = Storage(self.db_path)

    def tearDown(self):
        self.storage.close()
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_save_and_retrieve(self):
        snapshot = {
            "timestamp": "2026-06-03T10:00:00",
            "hostname": "test-server",
            "system": {"memory": {"percent": 50}},
            "alerts": [],
            "processes": [],
            "ports": [],
            "paths": [],
            "kanban": {},
        }
        check_id = self.storage.save_snapshot(snapshot)
        self.assertGreater(check_id, 0)

        recent = self.storage.get_recent(limit=5)
        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0]["hostname"], "test-server")

    def test_multiple_saves(self):
        for i in range(3):
            snapshot = {
                "timestamp": f"2026-06-03T10:0{i}:00",
                "hostname": "test-server",
                "system": {"memory": {"percent": 50 + i * 10}},
                "alerts": [],
            }
            self.storage.save_snapshot(snapshot)

        recent = self.storage.get_recent(10)
        self.assertEqual(len(recent), 3)

    def test_alert_history(self):
        # 保存有告警的记录
        snapshot = {
            "timestamp": "2026-06-03T10:00:00",
            "alerts": [{"level": "critical", "message": "test"}],
        }
        self.storage.save_snapshot(snapshot)

        history = self.storage.get_alert_history(days=7)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["alert_count"], 1)

    def test_cleanup_old(self):
        import sqlite3
        # 直接写入一条旧记录
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
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
        conn.execute(
            "INSERT INTO checks (timestamp, hostname, snapshot_json, alert_count) "
            "VALUES ('2020-01-01T00:00:00', 'old', '{}', 0)"
        )
        conn.commit()
        conn.close()

        # 重新实例化 storage
        self.storage = Storage(self.db_path)
        deleted = self.storage.cleanup_old(days=30)
        self.assertGreaterEqual(deleted, 1)

    def test_today_snapshots(self):
        snapshot = {
            "timestamp": "2026-06-03T10:00:00",
            "alerts": [],
        }
        self.storage.save_snapshot(snapshot)
        today = self.storage.get_today_snapshots()
        self.assertIsInstance(today, list)


if __name__ == "__main__":
    unittest.main(verbosity=2)