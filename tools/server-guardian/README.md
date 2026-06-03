# server-guardian

服务器智能健康检查系统 — 监控 + 告警推送 + 日报。

## 功能

- **健康检查**: CPU、内存、磁盘、Swap、负载、进程、端口、文件
- **进程监控**: 自动识别配置中的服务进程是否在运行
- **看板 DB 完整性检查**: 自动检测 SQLite 数据库损坏
- **看板备份状态检查**: 备份文件数量和时效性
- **分级告警**: Critical / Warning / Info 三级，推送飞书
- **日报生成**: 每天定时输出健康日报
- **历史记录**: SQLite 存储，支持趋势查询
- **配置驱动**: YAML 配置检查项和阈值

## 用法

```bash
# 单次检查
python3 main.py

# 连续监控
python3 main.py --daemon

# 生成日报
python3 main.py --report

# 仅采集（输出 JSON）
python3 main.py --snapshot
```

## 配置文件

编辑 `config.yaml` 设置阈值、监控项和推送目标。

## 依赖

- Python 3.8+
- PyYAML（`pip install pyyaml`）

## 部署

推荐通过 Hermes Cron 定时触发：

```bash
hermes cron create \
  --name server-guardian \
  --schedule "*/30 * * * *" \
  --command "python3 ~/server-guardian/main.py" \
  --deliver origin
```

同时设置日报：

```bash
hermes cron create \
  --name server-guardian-report \
  --schedule "0 23 * * *" \
  --command "python3 ~/server-guardian/main.py --report" \
  --deliver origin
```
