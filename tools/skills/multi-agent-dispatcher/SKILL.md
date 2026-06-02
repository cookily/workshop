---
name: multi-agent-dispatcher
description: 主网关 + Kanban 调度 + Hindsight 隔离的多 Agent 协作架构，搭建步骤和避坑指南
tags: [kanban, multi-agent, dispatcher, subagent, hospital-project]
---

# Multi-Agent Dispatcher 架构

主网关（default profile）作为调度官，通过 Hermes Kanban 分发任务给子 Agent profile，实现并行任务处理和记忆隔离。

## 架构图

```
用户（飞书）
    ↓
┌─────────────────────────────────────┐
│  主网关 default profile              │
│  bank: hermes（公共记忆）            │
│  职责：接收任务、Kanan调度           │
└────────┬────────────────────────────┘
         │ hermes kanban dispatch
         ↓
┌─────────────────────────────────────┐
│  Kanban 看板（多 board）             │
│  ├─ hospital-project               │
│  └─ side-project / 其他项目board    │
└────────┬────────────────────────────┘
         │ spawn（按 assignee 分发）
         ↓                   ↓
┌─────────────────┐  ┌─────────────────┐
│ hospital        │  │ side-project   │
│ bank: hospital  │  │ bank: side-proj │
│ 角色：医院专家   │  │ 角色：副业专家   │
└─────────────────┘  └─────────────────┘
```

## 核心概念

| 术语 | 含义 |
|------|------|
| **spawn** | 主进程创建新的独立子进程来处理任务，不同于线程隔离 |
| **dispatch** | 扫描 Kanban 所有 `ready` 任务，按 `assignee` 分发给对应 profile |
| **daemon 模式** | 常驻进程自动循环 dispatch，无需手动触发 |

## 适用场景

- 复杂项目需要多角色并行（架构师写设计、前端写页面、后端写接口）
- 需要记忆隔离的专业领域（医院项目 vs 副业项目）
- 耗时任务不希望阻塞主对话

## 快速开始

### 1. 创建子 Agent profile

```bash
hermes profile create <profile_name>
# 例如
hermes profile create hospital
hermes profile create side-project
```

### 2. 配置 providers（关键！）

子 profile **不继承** 主 `~/.hermes/config.yaml` 的 `providers:` 块，必须手动复制：

```bash
# 从主配置取出 providers 定义，追加到子 profile config.yaml
# 编辑 ~/.hermes/profiles/<profile_name>/config.yaml
# 在 model: 之前加入 providers: 完整定义（参考主配置）
```

**不复制会导致子 agent 启动时报 `Unknown provider 'xxx'`**

### 3. 配置记忆隔离（Hindsight）

```bash
hermes config set --profile <profile_name> memory.provider hindsight
hermes config set --profile <profile_name> memory.hindsight_bank_id <unique_bank_id>
hermes config set --profile <profile_name> memory.hindsight_mode local_external
```

每个子 profile 用独立的 bank_id，实现记忆隔离。

### 4. 编写角色定义

编辑 `~/.hermes/profiles/<profile_name>/SOUL.md`，定义：
- 核心能力（这个 agent 专注什么）
- 工作边界（不做什么）
- 协作方式（通过哪个 kanban board）
- 记忆规则（存入哪个 bank）

### 5. 创建 Kanban board

```bash
hermes kanban boards create <board_slug>
```

### 6. 手动调度（验证用）

```bash
# 创建任务，指定 assignee
hermes kanban --board <board> create "任务标题" --body "任务描述" --assignee <profile_name>

# 分发任务（手动模式）
hermes kanban --board <board> dispatch

# 查看任务状态
hermes kanban --board <board> show <task_id>

# 查看日志
cat ~/.hermes/kanban/boards/<board>/logs/<task_id>.log
```

### 7. 手动调度（验证用）

```bash
# 创建任务，指定 assignee
hermes kanban --board <board> create "任务标题" --body "任务描述" --assignee <profile_name> --priority 1
```

**注意**：`--priority` 接收整数（1=最高），不是 `high/medium/low` 字符串。`--tags` 参数不存在，不要使用。

### 8. 获取任务结果

任务完成后查看执行摘要：
```bash
hermes kanban show <task_id>
```

查看完整日志：
```bash
hermes kanban log <task_id>
```

读取产出物（工作目录在 `~/.hermes/kanban/workspaces/<task_id>/`，文件名含中文时经过 URL 编码）：
```bash
ls ~/.hermes/kanban/workspaces/<task_id>/
cat ~/.hermes/kanban/workspaces/<task_id>/*.md
```

## 调度模式对比

| 模式 | 触发方式 | 适用场景 |
|------|---------|---------|
| 手动 dispatch | 你或主网关执行 `hermes kanban dispatch` | 验证、测试、单次任务 |
| daemon | 常驻进程自动循环 | 长期运行、生产环境 |

## 回调通知：Mode A 和 Mode B 的区别

### Mode A（主网关转发）：不需要 notify-subscribe

主网关创建任务 → sub-agent 执行 → 状态变 done → **主网关主动感知** → 读 workspace → 转发用户。

**回调链路（不需要额外订阅）：**
```
sub-agent 完成任务 → workspace 写报告 → kanban 状态 done
                              ↓
主网关 poll/感知到 done → kanban show → 读 workspace → 转发用户
```

当前实现是**主动 poll**（dispatch 后主网关去查状态），未来可改进为进程退出信号触发。

### Mode B（直推用户）：用 notify-subscribe

如果想让 sub-agent 完成后**直接推送到你的飞书**，不走主网关：

```bash
hermes kanban notify-subscribe <task_id> \
  --platform feishu \
  --chat-id <your_chat_id> \
  --notifier-profile default
```

**注意**：Mode B 会让你的飞书收到两条消息（sub-agent 一条 + 主网关转发一条），体验不如 Mode A 干净。

### 选哪个

| 场景 | 模式 | 说明 |
|------|------|------|
| 统一体验，所有回复经过主网关 | Mode A | 主网关 poll，收到后转发 |
| sub-agent 直接推送，不经过主网关 | Mode B | 用 notify-subscribe |
| 快速验证，最小链路 | Mode A + 手动 `kanban show` | 不等回调，直接查 |

## Workspace 生命周期与交付物归档

Kanban workspace 是子 agent 执行任务时的**临时工作台**，不是永久存档。

### 特性

| 特性 | 说明 |
|------|------|
| 位置 | `~/.hermes/kanban/workspaces/<task_id>/` |
| 生命周期 | 与 task 同生命周期，不会自动删除但**也不是持久归档** |
| 用途 | 子 agent 下载资源、写脚本、生成报告的临时工作区 |
| 维护者 | Hermes 不自动清理，但也不保证永久保留（未来版本可能引入回收策略） |

### 推荐归档方式

任务产出物（报告、文档、代码）应转移到项目级目录，把 workspace 当作"草稿区"：

```bash
# 项目文档 → ~/docs/
cp ~/.hermes/kanban/workspaces/<task_id>/报告.md ~/docs/

# 代码产物 → 对应项目仓库
cp -r ~/.hermes/kanban/workspaces/<task_id>/src/* ~/projects/myapp/src/
```

### 实际案例

| 场景 | workspace 内容 | 归档目标 |
|------|---------------|---------|
| PACS 评分标准调研 | 214行报告 + PDF + Python脚本 | `~/docs/PACS招标评分标准调研报告.md` |
| 小红书种草笔记 | 3篇笔记 + 标题库 + 内容日历 | 可归档到项目目录或直接发飞书卡片 |

## 验证清单

- [ ] 子 profile 有独立 SOUL.md 角色定义
- [ ] 子 profile config.yaml 有完整 providers 定义
- [ ] 子 profile memory.hindsight_bank_id 设为独立值
- [ ] kanban board 创建成功
- [ ] 任务 create 时指定正确 assignee
- [ ] dispatch 后子 agent 进程被 spawn（ps aux 可见）
- [ ] 任务最终状态变为 `done`
- [ ] 子 agent 产出物在 workspace 目录

## 已知坑

### providers 不继承

子 profile 的 config.yaml 只覆盖了 `memory:` 和 `model:` 字段，但 `providers:` 定义在主 `~/.hermes/config.yaml` 里。子 agent 启动时不会自动继承，会报 `Unknown provider`。

**解法**：把主配置中完整的 `providers:` 块复制到子 profile 的 config.yaml。

### skills external_dirs 必须显式配置

子 profile 的 config.yaml 默认**不加载任何 skills 目录**，即使 skill 文件存在于 `~/.hermes/skills/`。启动时会报 `Unknown skill(s): <skill>`。

**症状**：
```
Error: Unknown skill(s): brainstorming
Error: Unknown skill(s): brainstorming   # 重复（重试两次后崩）
```

**解法**：在子 profile config.yaml 中显式添加两个 skills 目录：

```yaml
skills:
  external_dirs:
  - /home/ubuntu/.hermes/skills      # 324 skills (agency-agents-zh + superpowers-zh)
  - /home/ubuntu/.agents/skills       # mmx-cli 等外部工具
  template_vars: true
```

**两个目录都必须写**：
- `~/.hermes/skills/` — 324 个 skill（agency-agents-zh 215 + superpowers-zh 20 + 其他）
- `~/.agents/skills/` — mmx-cli 等工具型 skill

**验证**：
```bash
# 在子 profile 环境里测试 skill 是否可加载
hermes -p hospital skills list | grep brainstorming
```

### kanban 任务流转完整流程

**创建 → 分发 → 状态查询** 的正确命令顺序：

```bash
# 1. 创建任务（triage 状态）
hermes kanban create "任务标题" --assignee hospital --triage --skill brainstorming

# 2. 提升 triage → todo（specify 会填充 body 并改变状态）
hermes kanban specify <task_id>

# 3. 查看可用 board
hermes kanban boards list

# 4. 分发任务
hermes kanban dispatch

# 5. 查看状态
hermes kanban show <task_id>

# 6. 等待完成（进程存在 = 还在跑）
ps aux | grep <pid>   # pid 在 kanban show 的 spawned 事件里找
ls -la ~/.hermes/kanban/workspaces/<task_id>/  # 看工作区文件

# 7. 完成后读取产出
cat ~/.hermes/kanban/workspaces/<task_id>/*.md
```

**注意**：`claim` 不能用于 triage 状态的任务，必须用 `specify`。

### daemon 需要独立终端

`hermes kanban daemon` 是常驻进程，需要持续运行。放在后台或 screen/tmux 里。

### 任务无 body 会卡住

子 agent 收到 body 为空的任务时会卡在初始化阶段，不报错也不退出。

**解法**：创建任务时务必提供 `--body "具体任务描述"`。

### 子 agent 结果回报主网关再转用户（完整链路已验证）

```
你（飞书）→ 主网关 → kanban create → hospital sub-agent spawn → 执行 → workspace 写 .md
                                      ↑ 完成回调主网关（通过 kanban 状态更新）
主网关 → 你（飞书）→ kanban show + 读 workspace → 展示报告
```

**流程要点：**
1. 主网关收到任务 → `kanban create --assignee hospital` → 任务状态 `ready`
2. sub-agent 自动 pickup（daemon 模式）或手动 `dispatch` → 状态 `running`
3. sub-agent 独立进程运行 1-N 分钟 → 完成后 workspace 写报告 → 状态 `done`
4. 主网关 `kanban show <task_id>` 查看摘要 + 读 workspace 拿到完整报告
5. 主网关转发给用户

**任务创建命令（已验证可工作）：**
```bash
hermes kanban create "任务标题" \
  --assignee hospital \
  --priority 1 \
  --body "具体任务描述，越详细子agent越能准确执行"
```

sub-agent 运行结果在：
```
~/.hermes/kanban/workspaces/<task_id>/*.md
```

### 子 agent 运行在独立进程，不是独立窗口

用户的任务由主网关调度，子 agent **不在同一个飞书对话窗口里运行**。流程：

```
你 → 主网关（当前飞书窗口）
主网关 → spawn 子 agent（独立进程，独立终端会话）
子 agent → 执行任务 → 写结果到 workspace
主网关 → 把结果回报给你
```

子 agent 有自己的 CLI 界面，不绑定飞书 UI。你在飞书里看到的是**主网关的响应**，不是子 agent 的输出。

两个子 agent（医院项目 vs 副业项目）**同时在后台运行**（如果都有 ready 任务），不串行排队。

## 与 agency-orchestrator 的关系（重要补充）

**Kanban dispatch** 和 **agency-orchestrator** 是互补的两层：

| | Kanban Dispatch | agency-orchestrator |
|--|-----------------|---------------------|
| 定位 | 任务分发（谁来做） | 工作流编排（怎么做） |
| 执行粒度 | 整个任务派给一个 profile | 多个角色并行协作出一个方案 |
| 记忆 | Hindsight bank 隔离 | 无记忆（单次执行） |
| 跨会话 | ✅ 支持 | ❌ 不支持 |
| 适用场景 | 跨会话长期任务、项目跟踪 | 一次性复杂任务（PR审查、竞品分析、商业计划书） |

**组合使用**：Kanban 接收用户的长线任务 → 派给 hospital profile → profile 内部调用 `ao run` 执行多角色工作流。

```bash
# profile 内部执行 agency-orchestrator 工作流
ao run /home/ubuntu/agency-orchestrator/workflows/product-review.yaml \
  -i product_name="医院PACS系统" \
  -i target_market="二级医院"
```

### agency-orchestrator 已知坑（2026-05-18 实战补充）

#### 坑1：YAML 内 provider 字段优先级高于 CLI 参数

```yaml
# test.yaml
llm:
  provider: "hermes-cli"   # ← 写死在 YAML 里
```

```bash
ao run test.yaml --provider claude-code   # ❌ 不生效，YAML 优先
```

**解法**：直接修改 YAML 文件中的 `provider:` 字段。

#### 坑2：hermes-cli provider 需要 Nous OAuth 登录

`hermes -z` 模式走的是 Nous 云端代理服务，需要独立的 OAuth token，和 `~/.hermes/config.yaml` 里的 API key 是两套体系。

```bash
$ hermes auth status minimax
minimax: logged out   # ← 独立于 config.yaml 的 API key

$ hermes -z "你好" --model minimax/MiniMax-M2.7
# → stdout 为空，exit 0（根本没连上）
```

服务器环境无浏览器，无法完成 OAuth 流程，**hermes-cli provider 在此环境下永远返回空**。

**解法**：使用 `provider: "claude-code"`（需提前配置 MiniMax 模型到 Claude Code），或使用有 API key 的 provider（deepseek/openai 等）。

#### 坑3：--resume 断点重跑会重复执行已完成步骤

```bash
ao run test.yaml --resume last --from summary
# → 应该只重跑 summary，但实际从第一步重新跑
```

**解法**：写一个只包含目标步骤的小 YAML，单独执行。

#### 坑4：ao-output 输出目录

执行结果保存在 `~/ao-output/`（用户 home 目录），不是命令执行时的当前目录。

---

### agency-orchestrator 可用 provider（2026-05-18 实测）

| Provider | 状态 | 备注 |
|----------|------|------|
| claude-code | ✅ 可用 | 需提前在 Claude Code 配置 MiniMax 模型 |
| hermes-cli | ❌ 不可用 | 服务器环境无浏览器，无法 OAuth |
| deepseek | ✅ 可用 | 需 API key |
| openai | ✅ 可用 | 需 API key |

**推荐配置**（服务器无 API key 场景）：`provider: "claude-code"`，模型名格式 `minimax/MiniMax-M2.7`。

## Agent 通信协议选型参考

多 Agent 架构中，Agent 之间的通信方式决定了架构的灵活性、隔离性和性能。以下列出当前主流的协议，配合当前 dispatcher 架构的决策参考：

### 协议对比

| 协议 | 主导方 | 谁↔谁 | 传输层 | 场景 | 生态成熟度 |
|------|--------|-------|--------|------|-----------|
| **ACP** | Cursor | Agent ↔ Agent | stdio / WebSocket | 本地Agent编排（CLI子进程） | ✅ 生产可用 |
| **MCP** | Anthropic | Agent ↔ 工具/数据 | HTTP SSE / Streamable HTTP | Agent调工具、读数据源 | ✅ 生态最大 |
| **A2A** | Google | Agent ↔ Agent | HTTP REST | 跨网络/跨企业Agent协作 | 🆕 起步期 |
| **EventBus** | 自定义 | Master ↔ SubAgent | 进程内 channel | 内部广播、审计、前端实时推送 | 自建 |
| **LangGraph** | LangChain | Agent ↔ Agent | Python 内存 | 框架内图编排 | ✅ 开发者多 |

### 当前 dispatcher 实际使用的通信方式

| 链路 | 通信方式 | 说明 |
|------|---------|------|
| 用户 → 主网关 | Feishu Webhook / CLI | 用户通过飞书或终端发消息 |
| 主网关 → sub-agent | Kanban dispatch spawn 子进程 | Hermes kanban 创建任务 → spawn 独立进程 |
| sub-agent → workspace | 文件系统写 .md | sub-agent 执行完毕写报告到 workspace |
| 主网关 → 用户 | 读 workspace → 转发飞书 | 主网关 poll 到 done 后读 workspace 转给用户 |
| ACP 层（可选） | stdio JSON-line | 如果需要调 Claude Code / Codex 等外部 Agent |

### 各协议选型建议

```
你的场景 → 最优先考虑 → 原因
──────────────────────────────────
调度 Hermes 自己的 sub-agent → ACP（已经能用，Hermes CLI 有 acp 子命令）
让 Agent 用外部工具     → MCP（生态最大，Hermes 原生支持 MCP Client）
跨组织的 Agent 协作     → A2A（Google 推的，适合 HTTP 跨网络场景）
框架内多 Agent 图编排   → LangGraph（Python 生态成熟）
内部广播/审计/实时展示   → EventBus（自建，轻量进程内通信）
```

### agents-hive 的通信模式案例

agents-hive（Go 多 Agent 控制面）实现了 4 种通信方式的组合，可作为自己设计的参考：

| 通信方式 | 谁↔谁 | 实现位置 | 用途 |
|----------|-------|---------|------|
| **EventBus** | Master ↔ SubAgent | internal/master/eventBus | 进程内广播进度、审计事件到前端 |
| **SubAgent 回调** | Master ↔ 内置 SubAgent | internal/subagent/factory.go | explore/summary/title 等轻量Agent通过Go函数回调通信 |
| **ACP stdio** | agents-hive ↔ 外部 Agent | internal/acpclient/transport.go | 启动子进程（exec.Command），通过 stdin/stdout 传 JSON-line |
| **ACP WebSocket** | agents-hive ↔ 远程 Agent | internal/acpserver/session_bridge.go | 远程 ACP Session 绑定，带 token 认证 + 空闲 TTL 超时 |
| **WebSocket** | 后端 ↔ 浏览器 | internal/master/master.go: BroadcastMessage | 前端实时展示 Agent 进度 |

**值得借鉴的设计**：
- **BroadcastSessionMessage**：广播消息携带 SessionID，防止跨 session 泄漏（spec 12.4 contract）
- **进程内 SubAgent 走函数回调**：开销最低，适合 explore/summary 等轻量任务的内部协作
- **外部 Agent 走 ACP stdio**：通过 JSON-line 协议对接 Claude Code / Hermes / Codex，不改各自代码
- **SessionBridge 带 TTL**：acpserver 中绑定外部 session 时自动超时断开，防止僵尸连接

## 管理界面：hermes-web-ui（Web Dashboard）

[hermes-web-ui](https://github.com/EKKOLearnAI/hermes-web-ui)（EKKOLearnAI，6k+ star）是 Hermes Agent 的社区 Web 管理面板，提供多会话切换、Token 用量统计、平台配置、定时任务、群聊、文件浏览器等功能。

### 安装

```bash
npm install -g hermes-web-ui
hermes-web-ui start
# 默认 http://localhost:8648
```

### ⚠️ 网关冲突（常见陷阱）

hermes-web-ui 启动时会**自动扫描并启动所有 profile 的网关**。如果已有 systemd 网关（`hermes-gateway.service`）正在运行，两个网关共用同一个飞书 app_id，导致 Web UI 的飞书连接失败：

```
ERROR gateway.platforms.feishu: [Feishu] Another local Hermes gateway
is already using this Feishu app_id (PID xxx). Stop the other gateway
before starting a second Feishu websocket client.
```

**正确启动顺序**：

```bash
# 1. 停现有网关（飞书会话会断）
systemctl --user stop hermes-gateway.service

# 2. 启动 Web UI（它自己管网关）
hermes-web-ui start

# 3. 浏览器访问 http://<服务器IP>:8648
# 4. Token 在启动输出中，或 ~/.hermes-web-ui/.token

# 恢复原状：
hermes-web-ui stop
systemctl --user start hermes-gateway.service
```

### 会话可见性限制（v0.4.0）

Web UI 的会话侧边栏**只显示**自己产生的会话（API SERVER 来源）和 CLI 会话，**不显示**飞书/Telegram 等外部平台的历史会话。这些会话在 Hermes state.db 中，可通过 API 读取但不展示在侧边栏。

**查看方式**：
- Chat 页面新建会话后 Resume 历史会话
- 直接调用 API：`curl http://localhost:8648/api/hermes/sessions?limit=50`
- 或升级到新版（v0.6.1 可能已修复）

### Web UI 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `PORT` | `8648` | 监听端口 |
| `BIND_HOST` | `0.0.0.0` | 绑定地址 |
| `HERMES_WEB_UI_HOME` | `~/.hermes-web-ui` | 数据目录 |
| `PROFILE` | `default` | 启动 profile |
| `AUTH_TOKEN` | 自动生成 | 认证 Token |
| `LOG_LEVEL` | `info` | 日志级别 |

完整安装、配置和排错见 `references/hermes-web-ui.md`。

## 参考资料

- `references/agency-orchestrator-template.md` — 实测可用的 YAML 模板
- `references/mmx-vision-workaround.md` — vision_analyze 401 替代方案
- `references/soul-three-roles-template.md` — 角色专业化三角色模板
- `references/scale-engine-governance-pattern.md` — SCALE Engine 治理模式
- `references/agent-communication-protocols.md` — Agent 通信协议对比
- `references/hermes-web-ui.md` — Web 管理面板安装与排错详解

