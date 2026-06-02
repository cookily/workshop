# agents-hive — Go 多 Agent 生产底座

> "Agent Runtime + Agent Harness + Quality Control Plane + Ops Workbench"——把 Agent 从"会聊天会调工具"升级成可托管、可审计、可评估的复杂任务执行单元。

## 基本信息

| 字段 | 内容 |
|------|------|
| 仓库 | GitHub (`chef-guo/agents-hive`) + Gitee (`smart_kitchen/agents-hive`) — 均已删除 |
| 语言/框架 | Go 1.25+ / Node.js 22+ / React 19 / TypeScript 5.9 / PostgreSQL 16 / MinIO / Docker Compose |
| 研究日期 | 2026-05-19 |
| 研究方式 | 源码阅读 |
| 状态 | 🟡 留作参考，原项目已删除 |

> **状态**：GitHub (`chef-guo/agents-hive`) + Gitee (`smart_kitchen/agents-hive`) 均已删除
> **唯一来源**：`/home/ubuntu/agents-hive/`（本地 clone，Git 历史完整）
> **调研日期**：2026-05-19

## 一句话定位

"Agent Runtime + Agent Harness + Quality Control Plane + Ops Workbench"——把 Agent 从"会聊天会调工具"升级成可托管、可审计、可评估的复杂任务执行单元。

## 核心数据

- **1,097 个 Go 文件** + 194 个 TS/TSX 前端文件
- **59 个 internal 包**（master、subagent、agentquality、memory、llm 等）
- **技术栈**：Go 1.25+ / Node.js 22+ / React 19 / TypeScript 5.9 / PostgreSQL 16 / MinIO / Docker Compose

## 架构

```
Docker Compose: hive(postgres:16) → minio
                                        ↘ sandbox (DooD 模式，按需)
```

## 核心能力矩阵

| 能力 | 说明 |
|------|------|
| Agent Runtime | ReAct 主循环、工具调用、HITL、上下文压缩、长任务恢复 |
| Quality Control | Replay/Journal、质量事件、失败分类、回归样本、批量评测+回滚 |
| SubAgent/ACP | 内置 SubAgent（explore/summary/title/compaction）+ ACP协议对接外部Agent |
| IM Channel | 飞书、钉钉、企微、微信，统一会话权限审计HITL |
| Worker Hive | 本地 CLI/daemon 连中心控制面（nodes/task_queue 骨架，未完整闭环） |
| Ops Workbench | Web 控制台管理 LLM/Prompt/Skill/Channel/用户/配额 |
| Memory/Context | PostgreSQL 持久化，记忆治理，token accounting |

## 关键设计

### ACP（Agent Communication Protocol）
- `internal/acpclient/` + `internal/acpserver/`
- 支持 Cursor ACP 协议，可对接 Claude Code、Codex CLI、OpenCode、Hermes
- Web 控制台只能监管 agents-hive 自己调度的 Agent，不能监管 ACP 外部的 Agent

### 质量控制平面（最值得借鉴）
- Replay：回放整个 Agent 执行轨迹
- Journal：逐步骤日志
- 失败分类 + 回归样本
- 批量评测（`cmd/quality-batch-eval/`）
- 优化建议 + 人工审批 + rollback

### Sandbox 隔离
- DooD（Docker outside of Docker）模式
- 宿主 Docker socket 挂载到 hive 容器
- 每次任务创建独立 sandbox 容器

## 部署条件（本地服务器）

```
# 资源：RAM 2-4GB（主要为 PostgreSQL），磁盘 5-10GB+
# 依赖：Docker + Compose，LLM API Key（CLAW_API_KEY 或 OPENAI_API_KEY）
# 端口：8080（Web 控制台）
# 构建：make build-sandbox-image → docker compose up -d
```

## 跟 Hermes 的关系

| 维度 | Hermes | agents-hive |
|------|--------|-------------|
| 定位 | Agent CLI + 调度协调层 | Agent 控制面 + Ops 治理 |
| 部署 | 单进程 CLI + Gateway | Docker Compose 多服务 |
| Agent | Hermes 自己 + 子 Agent | Master/SubAgent + ACP 外部 Agent |
| 质量控制 | 无（Kanban 只跟踪状态） | 完整（Replay/Eval/回归） |
| IM 渠道 | 飞书 Gateway 接入 | 飞书/钉钉/企微/微信全通 |
| Web UI | 无 | React 19 控制台 |

**最值得借鉴的**：Quality Control Plane——把 Agent 执行过程变成可回放、可评估、可回归。

## 决策

> **结论**：🟡 留作参考，原项目已删除

**为什么**：agents-hive 的 Quality Control Plane（Replay/Journal/批量评测/回归）设计理念极具参考价值，但原项目在 GitHub 和 Gitee 上均已删除，目前仅存本地 clone。无法追踪最新发展或获取社区支持，因此仅作为设计参考存档，不纳入落地计划。

**后续动作**：
- [ ] 将 Quality Control Plane 的设计理念（Replay、Journal、失败分类、回归样本）记录到 Hermes 质量标准设计文档中
- [ ] 考虑在 Hermes 的 Kanban 系统中引入类似的 Agent 执行轨迹回放能力

**落地追踪**：
- 2026-05-19：首次分析 agents-hive