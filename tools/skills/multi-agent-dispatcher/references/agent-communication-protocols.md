# Agent Communication Protocols

参考来源：agents-hive 源码分析 + 业界主流协议调研

## 一、概述

当前 Agent 间通信没有唯一的行业标准，而是形成了几个互补协议，按场景选择。

```
通信类型            协议        场景
────────────────────────────────────────
Agent ↔ Agent      ACP / A2A   编排、委托、协作
Agent ↔ Tool       MCP         工具调用、数据查询
Agent ↔ 用户       WebSocket   前端实时展示
Agent ↔ 内部模块   EventBus    进程内广播、审计
```

## 二、ACP (Agent Communication Protocol)

**主导方**：Cursor (Anysphere)  
**定位**：Agent ↔ Agent 的本地通信协议  
**传输层**：stdio pipe / WebSocket  
**数据格式**：JSON-line (每行一个 JSON 消息)  
**支持者**：Cursor, Claude Code, Codex CLI, OpenCode, Hermes, agents-hive

### 原理

ACP 通过启动外部子进程（或连接远程 WebSocket），在主 Agent 与外部 Agent 之间建立双向通信管道。

```
主 Agent                   外部 Agent
   │     {"type":"run", "task":"..."}     │
   │─────────────────────────────────────→│
   │     {"type":"progress", "text":"..."}│
   │←─────────────────────────────────────│
   │     {"type":"result", "output":"..."}│
   │←─────────────────────────────────────│
```

### 实现模式

**Stdio 模式（本地）**：
- 主 Agent `exec.Command(command, args...)` 启动子进程
- 子进程 stdin 接收消息，stdout 发送消息
- 子进程退出时通信结束

**WebSocket 模式（远程）**：
- 主 Agent 通过 HTTP 升级到 WebSocket 连接远程 Agent
- 双向直接发送 JSON 结构体

### agents-hive 中的 ACP 实现

ACP 客户端 (`internal/acpclient/`)：
- `transport.go`：封装 stdio 双向管道（Reader/Writer/Closer）
- `remote_agent.go`：远程 Agent 连接管理
- `pool.go`：ACP 连接池管理

ACP 服务端 (`internal/acpserver/`)：
- `session_bridge.go`：SessionBridge 绑定外部 session，带 token 认证 + 空闲 TTL 超时断开
- `stream.go`：流式消息传输
- `mcp_passthrough.go`：MCP 穿透支持

## 三、MCP (Model Context Protocol)

**主导方**：Anthropic（2024年底推出）  
**定位**：Agent ↔ 工具/数据源的通信（**不是 Agent 间通信**）  
**传输层**：HTTP SSE / Streamable HTTP  
**数据格式**：JSON-RPC  
**支持者**：Claude Desktop, Claude Code, VS Code Copilot, Cursor, JetBrains, Sourcegraph Cody

### 架构

```
Agent (MCP Client) ←→ MCP Server (工具/数据源)
```

- Agent 通过 MCP Client 连接 MCP Server
- Server 暴露：`tools`（可调用的函数）、`resources`（可读取的数据）、`prompts`（可复用的提示模板）
- 支持通知（notifications）实现 Server 到 Client 的主动推送

### Hermes 集成

Hermes 原生支持 MCP Client，配置在 `~/.hermes/config.yaml` 的 `mcp_servers` 部分。

## 四、A2A (Agent-to-Agent Protocol)

**主导方**：Google（2025年4月推出）  
**定位**：Agent ↔ Agent 的企业级跨网络通信  
**传输层**：HTTP REST  
**数据格式**：JSON  
**认证**：OAuth 2.0  
**支持者**：Google (Vertex AI Agent, Gemini Agent)、Salesforce、LangChain、MongoDB

### 核心概念

- **Agent Card**：Agent 的能力宣告（JSON 格式，描述 Agent 能做什么）
- **Task-oriented delegation**：任务粒度的委托，不是会话粒度的
- **Ping/Pong**：心跳检测
- **OAuth 认证**：跨组织通信的安全保障

### 与 ACP 的对比

| 维度 | ACP | A2A |
|------|-----|-----|
| 创始人 | Cursor | Google |
| 传输层 | stdio / WebSocket | HTTP REST |
| 适用距离 | 本地/内网 | 跨网络/跨组织 |
| 认证 | 无/简单 token | OAuth 2.0 |
| 生态成熟度 | ✅ 生产可用 | 🆕 起步中 |
| 核心优势 | 低延迟、进程内 | 标准 HTTP、企业级认证 |
| Hermes 支持 | ✅ 原生支持 | ❌ 尚未支持 |

## 五、EventBus（进程内广播）

**定位**：同进程内 Agent ↔ 前端/审计/日志  
**传输层**：进程内 channel  
**特点**：零序列化开销、低延迟、不跨进程

### agents-hive 的 EventBus 设计

```
subagent 干活 → EventBus.BroadcastSessionMessage(消息)
                              ↓
        前端 WebSocket 订阅者收到 → 浏览器实时刷新
        日志端订阅者收到 → 写入审计日志
```

关键设计：`BroadcastSessionMessage` 携带 SessionID，防止跨 session 泄漏。

## 六、框架层 Agent 通信

| 框架 | 通信方式 | 特点 |
|------|---------|------|
| LangGraph | Python 函数调用 + StateGraph | 消息队列互通，有向图编排 |
| AutoGen (Microsoft) | 消息代理 + 组聊模式 | Agent 在 GroupChat 互发消息，speaker 选择 |
| CrewAI | 进程间函数调用 | 基于 Role 的任务委派 |
| OpenAI Assistants API | HTTP API + 线程/消息/运行 | 封闭生态，Thread-based 状态管理 |

## 七、选型决策树

```
需要 Agent 间通信吗？
├── 同进程内，轻量任务
│   └── → EventBus / 函数回调（如 agents-hive SubAgent）
├── 同机器，Agent 进程间
│   └── → ACP stdio（Hermes ↔ Claude Code / Codex）
├── 跨机器，同一组织内网
│   └── → ACP WebSocket
└── 跨组织，互联网级
    └── → A2A（HTTP REST + OAuth）

Agent 需要调外部工具/数据吗？
├── 是的 → MCP（生态最大，Hermes 原生支持）
└── 不需要 → 无需 MCP

需要前端实时展示 Agent 进度吗？
├── 需要 → WebSocket + EventBus
└── 不需要 → 仅 API 轮询
```