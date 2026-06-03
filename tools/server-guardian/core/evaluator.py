"""server-guardian/evaluator.py — 告警评估引擎

根据采集快照 + 阈值配置，生成分级告警列表。
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


def evaluate(snapshot: Dict[str, Any], config: dict) -> List[Dict[str, Any]]:
    """评估整个快照，返回告警列表（按严重级别排序）。

    每条告警格式：
        {
            "level": "critical" | "warning" | "info",
            "module": "memory" | "disk" | "process" | ...,
            "message": str,
            "current": Any,       # 当前值
            "threshold": Any,     # 触发阈
        }

    Args:
        snapshot: collect_all() 返回的健康快照。
        config: 解析后的配置字典。

    Returns:
        list[dict]: 按 severity 排序的告警列表。无告警为空列表。
    """
    alerts: List[Dict[str, Any]] = []
    thresholds = config.get("thresholds", {})

    # ── 内存检查 ──
    memory = snapshot.get("system", {}).get("memory", {})
    if memory:
        mem_pct = memory.get("percent", 0)
        _check_threshold(alerts, "memory", mem_pct, "内存使用率", "%",
                         thresholds.get("memory", {}))

    # ── Swap 检查 ──
    swap = snapshot.get("system", {}).get("swap", {})
    if swap:
        swap_pct = swap.get("percent", 0)
        _check_threshold(alerts, "swap", swap_pct, "Swap 使用率", "%",
                         thresholds.get("swap", {}))

    # ── CPU 检查 ──
    cpu = snapshot.get("system", {}).get("cpu", {})
    if cpu:
        cpu_pct = cpu.get("percent", 0)
        _check_threshold(alerts, "cpu", cpu_pct, "CPU 使用率", "%",
                         thresholds.get("cpu", {}))

    # ── 磁盘检查 ──
    disks = snapshot.get("system", {}).get("disk", [])
    for disk in disks:
        mount = disk.get("mount", "")
        disk_pct = disk.get("percent", 0)
        _check_threshold(alerts, f"disk:{mount}", disk_pct,
                         f"磁盘 {mount} 使用率", "%",
                         thresholds.get("disk", {}))

    # ── 负载检查 ──
    load = snapshot.get("system", {}).get("load_avg", {})
    if load:
        load_1min = load.get("1min", 0)
        _check_threshold(alerts, "load", load_1min, "系统负载(1min)", "",
                         thresholds.get("load", {}))

    # ── 进程数检查 ──
    proc_count = snapshot.get("system", {}).get("process_count")
    proc_warn = thresholds.get("process_count", {}).get("warning")
    if proc_count is not None and proc_warn and proc_count > proc_warn:
        alerts.append({
            "level": "warning",
            "module": "process_count",
            "message": f"系统进程数 {proc_count}，超过 {proc_warn} 阈值",
            "current": proc_count,
            "threshold": proc_warn,
        })

    # ── 进程状态检查 ──
    for proc in snapshot.get("processes", []):
        status = proc.get("status", "")
        name = proc.get("name", "unknown")
        if status == "down":
            alerts.append({
                "level": "critical",
                "module": f"process:{name}",
                "message": f"进程 {name} 未运行",
                "current": 0,
                "threshold": 1,
            })
        elif status == "partial":
            alerts.append({
                "level": "warning",
                "module": f"process:{name}",
                "message": f"进程 {name} 在运行但端口 {proc.get('port')} 未监听",
                "current": proc.get("port_open"),
                "threshold": True,
            })

    # ── 端口检查 ──
    for port_entry in snapshot.get("ports", []):
        port = port_entry.get("port")
        if not port_entry.get("open", False):
            alerts.append({
                "level": "warning",
                "module": f"port:{port}",
                "message": f"端口 {port} 未监听",
                "current": False,
                "threshold": True,
            })

    # ── 文件/路径检查 ──
    for path_entry in snapshot.get("paths", []):
        status = path_entry.get("status", "")
        desc = path_entry.get("description", path_entry.get("path", ""))
        if status == "missing":
            alerts.append({
                "level": "warning",
                "module": "path",
                "message": f"文件丢失: {desc}",
                "current": False,
                "threshold": True,
            })
        elif status == "corrupt":
            alerts.append({
                "level": "critical",
                "module": "path",
                "message": f"数据库损坏: {desc}",
                "current": path_entry.get("integrity", "unknown"),
                "threshold": "ok",
            })
        elif status == "too_large":
            size = path_entry.get("size_mb", 0)
            max_size = path_entry.get("max_size_mb", 0)
            alerts.append({
                "level": "warning",
                "module": "path",
                "message": f"文件过大: {desc} ({size}MB > {max_size}MB)",
                "current": size,
                "threshold": max_size,
            })

    # ── 看板备份检查 ──
    kb = snapshot.get("kanban", {})
    kb_status = kb.get("status", "")
    if kb_status == "missing":
        alerts.append({
            "level": "warning",
            "module": "kanban_backup",
            "message": f"看板备份目录不存在: {kb.get('dir', '')}",
            "current": "missing",
            "threshold": "exists",
        })
    elif kb_status == "too_few_backups":
        count = kb.get("file_count", 0)
        minimum = kb.get("min_files", 3)
        alerts.append({
            "level": "warning",
            "module": "kanban_backup",
            "message": f"看板备份文件不足: {count} 个 < {minimum} 个要求",
            "current": count,
            "threshold": minimum,
        })
    elif kb_status == "stale":
        age = kb.get("newest_age_hours", 0)
        max_age = kb.get("max_age_hours", 12)
        alerts.append({
            "level": "warning",
            "module": "kanban_backup",
            "message": f"看板备份过期: {age}小时前更新 > {max_age}小时阈值",
            "current": age,
            "threshold": max_age,
        })

    # ── 运行时间检查 ──
    uptime_sec = snapshot.get("uptime_seconds")
    uptime_warn = thresholds.get("uptime_days", {}).get("warning")
    if uptime_sec is not None and uptime_warn:
        uptime_days = uptime_sec / 86400
        if uptime_days > uptime_warn:
            alerts.append({
                "level": "info",
                "module": "uptime",
                "message": f"服务器已运行 {uptime_days:.0f} 天，超过 {uptime_warn} 天建议重启",
                "current": round(uptime_days, 0),
                "threshold": uptime_warn,
            })

    # 按严重级别排序：critical → warning → info
    severity_order = {"critical": 0, "warning": 1, "info": 2}
    alerts.sort(key=lambda a: severity_order.get(a.get("level", "info"), 99))

    return alerts


def _check_threshold(
    alerts: List[Dict[str, Any]],
    module: str,
    current: float,
    label: str,
    unit: str,
    thresholds: dict,
) -> None:
    """检查单指标阈值，有超则追加告警。"""
    critical = thresholds.get("critical")
    warning = thresholds.get("warning")

    if critical is not None and current >= critical:
        alerts.append({
            "level": "critical",
            "module": module,
            "message": f"{label} {current}{unit}，超过严重阈值 {critical}{unit}",
            "current": current,
            "threshold": critical,
        })
    elif warning is not None and current >= warning:
        alerts.append({
            "level": "warning",
            "module": module,
            "message": f"{label} {current}{unit}，超过警告阈值 {warning}{unit}",
            "current": current,
            "threshold": warning,
        })