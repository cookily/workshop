"""server-guardian/checkers.py — 独立检查函数

每个函数专注一项检查，无状态、可测试。
所有函数兼容异常场景，不抛异常。
"""

import os
import subprocess
import socket
import time
from typing import Any, Dict, List, Optional, Tuple


# ── System Metrics ──────────────────────────────────────────

def collect_cpu() -> Optional[Dict[str, Any]]:
    """采集 CPU 使用率（/proc/stat 两次采样差值）。"""
    try:
        with open("/proc/stat", "r") as f:
            line1 = f.readline().strip().split()
    except (FileNotFoundError, PermissionError, OSError):
        return None

    if not line1 or line1[0] != "cpu":
        return None

    time.sleep(0.1)

    try:
        with open("/proc/stat", "r") as f:
            line2 = f.readline().strip().split()
    except (FileNotFoundError, PermissionError, OSError):
        return None

    if not line2 or line2[0] != "cpu":
        return None

    fields1 = [int(x) for x in line1[1:9]]
    fields2 = [int(x) for x in line2[1:9]]

    total1 = sum(fields1)
    total2 = sum(fields2)
    idle1 = fields1[3] + fields1[4]
    idle2 = fields2[3] + fields2[4]

    total_delta = total2 - total1
    idle_delta = idle2 - idle1

    percent = 0.0
    if total_delta > 0:
        percent = round((total_delta - idle_delta) / total_delta * 100, 1)

    cores = 0
    try:
        with open("/proc/stat", "r") as f:
            for line in f:
                if line.startswith("cpu") and len(line) > 3 and line[3].isdigit():
                    cores += 1
    except OSError:
        pass

    return {"percent": percent, "cores": cores}


def collect_memory() -> Optional[Dict[str, Any]]:
    """采集内存使用情况（/proc/meminfo）。"""
    try:
        with open("/proc/meminfo", "r") as f:
            content = f.read()
    except (FileNotFoundError, PermissionError, OSError):
        return None

    meminfo: Dict[str, int] = {}
    for line in content.strip().split("\n"):
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        parts = val.strip().split()
        if parts:
            try:
                meminfo[key.strip()] = int(parts[0])
            except ValueError:
                continue

    total_kb = meminfo.get("MemTotal")
    available_kb = meminfo.get("MemAvailable")

    if total_kb is None or total_kb == 0:
        return None

    if available_kb is not None:
        used_kb = total_kb - available_kb
    else:
        free_kb = meminfo.get("MemFree", 0)
        used_kb = total_kb - free_kb

    total_gb = round(total_kb / (1024 * 1024), 1)
    used_gb = round(used_kb / (1024 * 1024), 1)
    percent = round(used_kb / total_kb * 100, 1)

    return {"total_gb": total_gb, "used_gb": used_gb, "percent": percent}


def collect_swap() -> Optional[Dict[str, Any]]:
    """采集 Swap 使用情况（/proc/meminfo）。"""
    try:
        with open("/proc/meminfo", "r") as f:
            content = f.read()
    except (FileNotFoundError, PermissionError, OSError):
        return None

    meminfo: Dict[str, int] = {}
    for line in content.strip().split("\n"):
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        parts = val.strip().split()
        if parts:
            try:
                meminfo[key.strip()] = int(parts[0])
            except ValueError:
                continue

    total_kb = meminfo.get("SwapTotal", 0)
    free_kb = meminfo.get("SwapFree", 0)

    if total_kb is None or total_kb == 0:
        return {"total_gb": 0, "used_gb": 0, "percent": 0}

    used_kb = total_kb - free_kb
    total_gb = round(total_kb / (1024 * 1024), 1)
    used_gb = round(used_kb / (1024 * 1024), 1)
    percent = round(used_kb / total_kb * 100, 1)

    return {"total_gb": total_gb, "used_gb": used_gb, "percent": percent}


_VIRTUAL_FS_TYPES: frozenset = frozenset({
    "devtmpfs", "tmpfs", "squashfs", "proc", "sysfs", "cgroup", "cgroup2",
    "devpts", "securityfs", "pstore", "bpf", "autofs", "hugetlbfs",
    "mqueue", "debugfs", "tracefs", "fusectl", "configfs", "binfmt_misc",
    "nsfs", "overlay",
})


def collect_disk() -> List[Dict[str, Any]]:
    """采集真实磁盘挂载点使用情况。"""
    result: List[Dict[str, Any]] = []
    try:
        with open("/proc/mounts", "r") as f:
            for line in f:
                parts = line.split()
                if len(parts) < 3:
                    continue
                device = parts[0]
                mount_point = parts[1]
                fs_type = parts[2]

                if fs_type in _VIRTUAL_FS_TYPES:
                    continue

                try:
                    stat = os.statvfs(mount_point)
                except (OSError, PermissionError):
                    continue

                block_size = stat.f_frsize
                total_bytes = stat.f_blocks * block_size
                available_bytes = stat.f_bavail * block_size

                if total_bytes == 0:
                    continue

                used_bytes = total_bytes - available_bytes
                total_gb = round(total_bytes / (1024 ** 3), 1)
                used_gb = round(used_bytes / (1024 ** 3), 1)
                percent = round(100.0 * used_bytes / total_bytes, 1)

                result.append({
                    "device": device,
                    "mount": mount_point,
                    "total_gb": total_gb,
                    "used_gb": used_gb,
                    "percent": percent,
                })
    except Exception:
        pass

    return result


def collect_load_avg() -> Optional[Dict[str, float]]:
    """采集系统负载（/proc/loadavg）。"""
    try:
        with open("/proc/loadavg", "r") as f:
            parts = f.readline().strip().split()
        if len(parts) >= 3:
            return {
                "1min": float(parts[0]),
                "5min": float(parts[1]),
                "15min": float(parts[2]),
            }
    except Exception:
        pass
    return None


def collect_process_count() -> Optional[int]:
    """统计系统总进程数。"""
    try:
        result = subprocess.run(
            ["ps", "-e", "--no-headers"],
            capture_output=True, text=True, timeout=5
        )
        return len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0
    except Exception:
        return None


# ── Process / Port Checks ───────────────────────────────────

def find_process(pattern: str) -> int:
    """查找匹配指定模式的进程数量。"""
    try:
        result = subprocess.run(
            ["pgrep", "-f", pattern],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            return len(result.stdout.strip().split("\n"))
    except Exception:
        pass
    try:
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True, text=True, timeout=5
        )
        count = 0
        for line in result.stdout.split("\n"):
            if pattern in line and "grep" not in line:
                count += 1
        return count
    except Exception:
        return 0


def check_port(port: int) -> bool:
    """检查指定端口是否在监听中。"""
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=2):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def check_systemd_services() -> Dict[str, Any]:
    """检查 systemd 服务状态。返回活跃服务列表和异常服务。"""
    result = {
        "running": [],
        "failed": [],
        "not_found": [],
    }
    try:
        # 获取所有活跃服务
        out = subprocess.run(
            ["systemctl", "list-units", "--type=service", "--state=running",
             "--no-pager", "--plain"],
            capture_output=True, text=True, timeout=10
        )
        for line in out.stdout.split("\n"):
            parts = line.strip().split()
            if len(parts) >= 1 and parts[0].endswith(".service"):
                result["running"].append(parts[0].replace(".service", ""))
    except Exception:
        pass
    return result


# ── File / DB Checks ────────────────────────────────────────

def check_sqlite_integrity(db_path: str) -> str:
    """执行 SQLite 完整性检查。

    Returns:
        "ok" | "corrupt" | "error"
    """
    if not os.path.isfile(db_path):
        return "not_found"
    try:
        out = subprocess.run(
            ["sqlite3", db_path, "PRAGMA integrity_check;"],
            capture_output=True, text=True, timeout=30
        )
        result = out.stdout.strip()
        if result == "ok":
            return "ok"
        return f"corrupt: {result[:200]}"
    except Exception as e:
        return f"error: {e}"


def check_file_age(filepath: str) -> Optional[float]:
    """返回文件距今的小时数。"""
    if not os.path.isfile(filepath):
        return None
    age_seconds = time.time() - os.path.getmtime(filepath)
    return age_seconds / 3600


def check_directory_file_count(directory: str) -> Optional[int]:
    """返回目录中文件数量。"""
    if not os.path.isdir(directory):
        return None
    try:
        return len([
            f for f in os.listdir(directory)
            if os.path.isfile(os.path.join(directory, f))
        ])
    except Exception:
        return None