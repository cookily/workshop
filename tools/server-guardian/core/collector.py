"""server-guardian/collector.py — 采集调度引擎

将配置驱动的检查项转换为结构化的健康数据快照。
"""

import os
import time
import socket
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from . import checkers


def collect_all(config: dict) -> Dict[str, Any]:
    """执行全套健康检查，返回结构化快照。

    Args:
        config: 解析后的 config.yaml 字典。

    Returns:
        dict: 包含所有模块采集结果的完整快照。
    """
    snapshot: Dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hostname": socket.gethostname(),
        "uptime_seconds": _get_uptime(),
        "system": _collect_system(),
        "processes": _collect_processes(config),
        "ports": _collect_ports(config),
        "paths": _collect_paths(config),
        "kanban": _collect_kanban_backup(config),
        "disk_growth": _collect_disk_growth(config),
    }
    # 服务状态汇总（从 systemd 检查）
    snapshot["services"] = checkers.check_systemd_services()
    return snapshot


def _get_uptime() -> Optional[float]:
    """读取系统运行时间（秒）。"""
    try:
        with open("/proc/uptime", "r") as f:
            return float(f.readline().split()[0])
    except Exception:
        return None


def _collect_system() -> Dict[str, Any]:
    """采集系统级指标：CPU、内存、磁盘、Swap、负载。"""
    cpu = checkers.collect_cpu()
    memory = checkers.collect_memory()
    disk = checkers.collect_disk()
    swap = checkers.collect_swap()
    load = checkers.collect_load_avg()
    proc_count = checkers.collect_process_count()

    return {
        "cpu": cpu,
        "memory": memory,
        "disk": disk,
        "swap": swap,
        "load_avg": load,
        "process_count": proc_count,
    }


def _collect_processes(config: dict) -> List[Dict[str, Any]]:
    """检查配置中的进程列表是否在运行。"""
    results: List[Dict[str, Any]] = []
    processes = config.get("processes", [])
    for proc in processes:
        name = proc.get("name", "unknown")
        pattern = proc.get("pattern", name)
        port = proc.get("port")
        count_min = proc.get("count_min", 1)

        running_count = checkers.find_process(pattern)
        port_open = checkers.check_port(port) if port else None

        status = "ok"
        if running_count < count_min:
            status = "down"
        elif port is not None and not port_open:
            status = "partial"  # 进程在但端口没监听

        results.append({
            "name": name,
            "pattern": pattern,
            "running_count": running_count,
            "port_open": port_open,
            "port": port,
            "status": status,
        })
    return results


def _collect_ports(config: dict) -> List[Dict[str, Any]]:
    """检查配置中的端口是否在监听。"""
    results: List[Dict[str, Any]] = []
    ports = config.get("ports", [])
    for port in ports:
        is_open = checkers.check_port(port)
        results.append({
            "port": port,
            "open": is_open,
        })
    return results


def _collect_paths(config: dict) -> List[Dict[str, Any]]:
    """检查配置中的文件/路径状态。"""
    results: List[Dict[str, Any]] = []
    paths = config.get("paths", [])
    for entry in paths:
        raw_path = entry.get("path", "")
        description = entry.get("description", raw_path)
        max_size_mb = entry.get("max_size_mb")
        check_integrity = entry.get("check_integrity", False)

        full_path = os.path.expanduser(raw_path)
        exists = os.path.exists(full_path)
        info: Dict[str, Any] = {
            "path": raw_path,
            "description": description,
            "exists": exists,
        }

        if exists and os.path.isfile(full_path):
            size_bytes = os.path.getsize(full_path)
            size_mb = round(size_bytes / (1024 * 1024), 2)
            info["size_mb"] = size_mb
            info["modified"] = datetime.fromtimestamp(
                os.path.getmtime(full_path), tz=timezone.utc
            ).isoformat()

            if max_size_mb and size_mb > max_size_mb:
                info["status"] = "too_large"
                info["max_size_mb"] = max_size_mb
            elif check_integrity and full_path.endswith(".db"):
                info["integrity"] = checkers.check_sqlite_integrity(full_path)
                info["status"] = "ok" if info.get("integrity") == "ok" else "corrupt"
            else:
                info["status"] = "ok"
        elif exists and os.path.isdir(full_path):
            info["status"] = "ok"
        else:
            info["status"] = "missing"

        results.append(info)
    return results


def _collect_kanban_backup(config: dict) -> Dict[str, Any]:
    """检查看板备份目录状态。"""
    backup_cfg = config.get("kanban_backup", {})
    backup_dir = os.path.expanduser(backup_cfg.get("dir", ""))
    if not backup_dir or not os.path.isdir(backup_dir):
        return {"status": "missing", "dir": backup_cfg.get("dir", "")}

    try:
        files = sorted([
            f for f in os.listdir(backup_dir)
            if os.path.isfile(os.path.join(backup_dir, f))
        ])
    except Exception:
        return {"status": "error", "dir": backup_dir}

    file_count = len(files)
    min_files = backup_cfg.get("min_files", 3)
    max_age_hours = backup_cfg.get("max_age_hours", 12)

    result = {
        "dir": backup_dir,
        "file_count": file_count,
        "min_files": min_files,
        "status": "ok",
    }

    if file_count < min_files:
        result["status"] = "too_few_backups"

    if files:
        newest = os.path.join(backup_dir, files[-1])
        age_seconds = time.time() - os.path.getmtime(newest)
        age_hours = age_seconds / 3600
        result["newest_age_hours"] = round(age_hours, 1)
        result["newest_file"] = files[-1]

        if max_age_hours and age_hours > max_age_hours:
            result["status"] = "stale"
            result["max_age_hours"] = max_age_hours

        oldest = os.path.join(backup_dir, files[0])
        oldest_age_days = (time.time() - os.path.getmtime(oldest)) / 86400
        result["oldest_age_days"] = round(oldest_age_days, 1)

    return result


def _collect_disk_growth(config: dict) -> Optional[Dict[str, Any]]:
    """估算 24 小时磁盘增长量（基于当前使用率和前后两次采集的差值）。

    需要历史数据支持；本次仅做标记，由 evaluator 检查趋势。
    """
    disk = checkers.collect_disk()
    for entry in disk:
        if entry.get("mount") == "/":
            return {
                "mount": "/",
                "current_used_gb": entry.get("used_gb", 0),
                "growth_24h_gb": None,  # 由 evaluator 填充
            }
    return None
