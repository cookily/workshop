"""server-guardian/report/daily.py — 日报生成

从存储的历史数据中生成结构化的健康日报文本。
"""

import os
import sys
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

# 确保项目根目录在 sys.path 中
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from storage.db import Storage
from alert.feishu import format_for_daily_report


def generate_report(
    storage: Storage,
    alerts: List[Dict[str, Any]],
    snapshot: Dict[str, Any],
    report_dir: str,
) -> str:
    """生成健康日报并写入文件。

    Args:
        storage: Storage 实例。
        alerts: 当前告警列表。
        snapshot: 当前快照。
        report_dir: 日报输出目录。

    Returns:
        str: 日报文本内容。
    """
    tz = timezone(timedelta(hours=8))
    now = datetime.now(tz)

    # 获取今日所有检查记录
    today_checks = storage.get_today_snapshots()
    today_count = len(today_checks)

    # 格式化日报内容
    body = format_for_daily_report(alerts, snapshot, today_count)

    # 补充趋势数据
    if len(today_checks) >= 2:
        first = today_checks[0].get("snapshot", {})
        last = today_checks[-1].get("snapshot", {})
        body += _format_trend(first, last)

    # 补充长期统计
    week_alerts = storage.get_alert_history(days=7)
    if week_alerts:
        critical_count = sum(
            1 for r in week_alerts
            for a in r.get("alerts", [])
            if a.get("level") == "critical"
        )
        warning_count = sum(
            1 for r in week_alerts
            for a in r.get("alerts", [])
            if a.get("level") == "warning"
        )
        body += (
            f"\n━━━ 近7天统计 ━━━\n"
            f"  严重告警: {critical_count} 次\n"
            f"  警告告警: {warning_count} 次\n"
            f"  告警记录: {len(week_alerts)} 条"
        )

    # 写入文件
    date_str = now.strftime("%Y-%m-%d")
    report_dir_exp = os.path.expanduser(report_dir)
    os.makedirs(report_dir_exp, exist_ok=True)
    filepath = os.path.join(report_dir_exp, f"health-{date_str}.md")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# 服务器健康日报 — {date_str}\n\n")
        f.write(body)
        f.write(f"\n\n---\n*生成时间: {now.isoformat()}*")

    return body


def _format_trend(first: Dict[str, Any], last: Dict[str, Any]) -> str:
    """计算两次采集间的趋势变化。"""
    lines: List[str] = ["\n━━━ 趋势变化 ━━━"]

    def _safe_get(snap: dict, *keys):
        val = snap
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k)
            else:
                return None
        return val

    # 磁盘趋势
    first_disk = _safe_get(first, "system", "disk")
    last_disk = _safe_get(last, "system", "disk")
    if first_disk and last_disk:
        for f_d, l_d in zip(first_disk, last_disk):
            if f_d.get("mount") == l_d.get("mount") and f_d.get("mount") == "/":
                diff = l_d.get("used_gb", 0) - f_d.get("used_gb", 0)
                if abs(diff) > 0.1:
                    direction = "↑" if diff > 0 else "↓"
                    lines.append(f"  磁盘 {direction} {abs(diff):.1f}G")
                    break

    # 内存趋势
    first_mem = _safe_get(first, "system", "memory", "percent")
    last_mem = _safe_get(last, "system", "memory", "percent")
    if first_mem is not None and last_mem is not None:
        diff = last_mem - first_mem
        if abs(diff) > 3:
            direction = "↑" if diff > 0 else "↓"
            lines.append(f"  内存 {direction} {abs(diff):.1f}%")

    return "\n".join(lines) if len(lines) > 1 else ""