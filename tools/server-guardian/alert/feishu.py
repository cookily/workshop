"""server-guardian/alert/feishu.py — 飞书消息推送

将告警和日报以飞书消息卡片形式推送。
依赖 Hermes Agent 的 send_message 能力（运行时由 main 传入）。
"""

import sys
from datetime import datetime, timezone, timedelta
from typing import Any, Callable, Dict, List, Optional


class FeishuNotifier:
    """飞书推送器。

    将告警列表格式化为消息文本，通过回调函数发送。
    """

    def __init__(
        self,
        send_fn: Callable,
        target: str,
    ):
        self._send_fn = send_fn
        self._target = target

    def send_alerts(self, alerts: List[Dict[str, Any]]) -> bool:
        """推送告警消息到飞书。

        Args:
            alerts: evaluator.evaluate() 返回的告警列表。

        Returns:
            是否成功发送。
        """
        if not alerts:
            return False

        now = datetime.now(timezone(timedelta(hours=8))).strftime("%H:%M")
        criticals = [a for a in alerts if a.get("level") == "critical"]
        warnings = [a for a in alerts if a.get("level") == "warning"]
        infos = [a for a in alerts if a.get("level") == "info"]

        lines = [f"🚨 服务器告警 — {now}"]
        if criticals:
            lines.append(f"\n🔴 严重 ({len(criticals)}):")
            for a in criticals:
                lines.append(f"  • {a['message']}")
        if warnings:
            lines.append(f"\n🟡 警告 ({len(warnings)}):")
            for a in warnings:
                lines.append(f"  • {a['message']}")
        if infos:
            lines.append(f"\n🔵 提示 ({len(infos)}):")
            for a in infos:
                lines.append(f"  • {a['message']}")

        message = "\n".join(lines)
        return self._send(message)

    def send_daily_report(self, report: str) -> bool:
        """推送日报摘要到飞书。

        Args:
            report: 格式化的日报文本。

        Returns:
            是否成功发送。
        """
        header = "📊 服务器健康日报"
        now = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M")
        message = f"{header}\n{now}\n\n{report}"
        return self._send(message)

    def send_single_alert(self, alert: Dict[str, Any]) -> bool:
        """推送单条告警（紧急告警用）。"""
        now = datetime.now(timezone(timedelta(hours=8))).strftime("%H:%M")
        level = alert.get("level", "info")
        icon = {"critical": "🔴", "warning": "🟡", "info": "🔵"}.get(level, "ℹ️")
        message = (
            f"{icon} 服务器告警 — {now}\n"
            f"模块: {alert.get('module', 'unknown')}\n"
            f"{alert.get('message', '')}"
        )
        return self._send(message)

    def _send(self, message: str) -> bool:
        """实际发送消息。"""
        try:
            self._send_fn(target=self._target, message=message)
            return True
        except Exception:
            return False


def format_for_daily_report(
    alerts: List[Dict[str, Any]],
    snapshot: Dict[str, Any],
    today_count: int,
) -> str:
    """将健康检查结果格式化为日报文本。"""
    system = snapshot.get("system", {})
    memory = system.get("memory", {})
    disk = system.get("disk", [])
    load = system.get("load_avg", {})
    cpu = system.get("cpu", {})
    swap = system.get("swap", {})

    lines: List[str] = []

    # 概览
    lines.append("━━━ 系统概览 ━━━")
    if memory:
        lines.append(f"内存: {memory.get('used_gb', '?')}G/{memory.get('total_gb', '?')}G "
                      f"({memory.get('percent', '?')}%)")
    if swap:
        lines.append(f"Swap: {swap.get('used_gb', '?')}G/{swap.get('total_gb', '?')}G "
                      f"({swap.get('percent', '?')}%)")
    if cpu:
        lines.append(f"CPU: {cpu.get('percent', '?')}% ({cpu.get('cores', '?')}核)")
    if load:
        lines.append(f"负载: {load.get('1min', '?')} / {load.get('5min', '?')} / {load.get('15min', '?')}")
    for d in disk:
        if d.get("mount") == "/":
            lines.append(f"磁盘: {d.get('used_gb', '?')}G/{d.get('total_gb', '?')}G "
                          f"({d.get('percent', '?')}%)")

    # 进程状态
    procs = snapshot.get("processes", [])
    down = [p for p in procs if p.get("status") in ("down", "partial")]
    if down:
        lines.append(f"\n━━━ 异常进程 ({len(down)}) ━━━")
        for p in down:
            lines.append(f"  • {p['name']}: {p['status']}")

    # 今日告警
    lines.append(f"\n━━━ 告警汇总 ({len(alerts)}) ━━━")
    if alerts:
        for a in alerts:
            icon = {"critical": "🔴", "warning": "🟡", "info": "🔵"}.get(
                a.get("level", "info"), "ℹ️"
            )
            lines.append(f"  {icon} {a['message']}")
    else:
        lines.append("  ✅ 无告警")

    lines.append(f"\n━━━ 检查次数 ━━━")
    lines.append(f"  今日已执行 {today_count} 次健康检查")

    return "\n".join(lines)