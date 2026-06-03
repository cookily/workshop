#!/usr/bin/env python3
"""server-guardian — 服务器智能健康检查

用法:
    python3 main.py                      # 单次检查 (采集+告警+推送)
    python3 main.py --daemon              # 连续检查模式 (按间隔循环)
    python3 main.py --report              # 仅生成日报
    python3 main.py --snapshot            # 仅采集，输出 JSON

配置:
    config.yaml   — 检查项、阈值、推送目标
"""

import argparse
import json
import os
import sys
import time
import yaml
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

# 确保项目根目录在 sys.path 中
_project_root = os.path.dirname(os.path.abspath(__file__))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from core.collector import collect_all
from core.evaluator import evaluate
from storage.db import Storage
from alert.feishu import FeishuNotifier, format_for_daily_report
from report.daily import generate_report


def load_config(config_path: str) -> dict:
    """从 YAML 加载配置。"""
    path = os.path.expanduser(config_path)
    if not os.path.isfile(path):
        print(f"配置文件不存在: {path}", file=sys.stderr)
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_feishu_notifier(config: dict) -> Optional[FeishuNotifier]:
    """初始化飞书推送器。"""
    feishu_cfg = config.get("feishu", {})
    if not feishu_cfg.get("enabled", True):
        return None
    target = feishu_cfg.get("target", "")
    if not target:
        return None

    # send_message 的回调包装
    def send(target, message):
        from hermes_tools import send_message
        send_message(target=target, message=message)

    return FeishuNotifier(send, target)


def run_single_check(
    config: dict,
    storage: Storage,
    notifier: Optional[FeishuNotifier],
    report_dir: str,
) -> Dict[str, Any]:
    """执行一次完整的检查流程：采集 → 评估 → 存储 → 推送。"""
    # 1. 采集
    snapshot = collect_all(config)

    # 2. 评估
    alerts = evaluate(snapshot, config)

    # 3. 关联告警
    snapshot["alerts"] = alerts

    # 4. 存储
    check_id = storage.save_snapshot(snapshot)

    # 5. 推送（只在有告警时推送）
    if alerts and notifier:
        notifier.send_alerts(alerts)

    # 6. 日志
    print(f"[{datetime.now(timezone(timedelta(hours=8))).strftime('%H:%M:%S')}] "
          f"检查 #{check_id}: {len(alerts)} 条告警", file=sys.stderr)

    return snapshot


def cmd_single(config: dict) -> None:
    """单次检查模式。"""
    data_dir = os.path.expanduser(config.get("general", {}).get("data_dir", "~/docs/server-guardian"))
    storage = Storage(os.path.join(data_dir, "history.db"))
    notifier = get_feishu_notifier(config)
    report_dir = os.path.join(data_dir, "reports")

    snapshot = run_single_check(config, storage, notifier, report_dir)

    # 输出 JSON 到 stdout
    print(json.dumps(snapshot, ensure_ascii=False, indent=2))


def cmd_daemon(config: dict) -> None:
    """守护模式：按间隔循环检查。"""
    data_dir = os.path.expanduser(config.get("general", {}).get("data_dir", "~/docs/server-guardian"))
    interval = config.get("general", {}).get("check_interval", 300)
    storage = Storage(os.path.join(data_dir, "history.db"))
    notifier = get_feishu_notifier(config)
    report_dir = os.path.join(data_dir, "reports")

    print(f"守护模式启动，间隔 {interval}s", file=sys.stderr)

    while True:
        try:
            run_single_check(config, storage, notifier, report_dir)
        except KeyboardInterrupt:
            print("\n正常退出", file=sys.stderr)
            break
        except Exception as e:
            print(f"检查执行失败: {e}", file=sys.stderr)

        time.sleep(interval)


def cmd_report(config: dict) -> None:
    """生成日报模式。"""
    data_dir = os.path.expanduser(config.get("general", {}).get("data_dir", "~/docs/server-guardian"))
    storage = Storage(os.path.join(data_dir, "history.db"))
    notifier = get_feishu_notifier(config)
    report_dir = os.path.join(data_dir, "reports")

    # 先做一次检查获取最新数据
    snapshot = run_single_check(config, storage, notifier, report_dir)
    alerts = snapshot.get("alerts", [])

    # 生成日报
    report_text = generate_report(storage, alerts, snapshot, report_dir)

    # 推送日报
    if notifier:
        notifier.send_daily_report(report_text)

    print(report_text)


def cmd_snapshot(config: dict) -> None:
    """仅采集模式，输出 JSON。"""
    snapshot = collect_all(config)
    print(json.dumps(snapshot, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="server-guardian — 服务器智能健康检查",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--config",
        default="~/server-guardian/config.yaml",
        help="配置文件路径 (默认: ~/server-guardian/config.yaml)",
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="连续检查模式",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="生成日报",
    )
    parser.add_argument(
        "--snapshot",
        action="store_true",
        help="仅采集输出 JSON",
    )

    args = parser.parse_args()
    config = load_config(args.config)

    if args.daemon:
        cmd_daemon(config)
    elif args.report:
        cmd_report(config)
    elif args.snapshot:
        cmd_snapshot(config)
    else:
        cmd_single(config)


if __name__ == "__main__":
    main()