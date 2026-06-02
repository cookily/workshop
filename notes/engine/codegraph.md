# CodeGraph

> 代码知识图谱 MCP 服务 — 用 tree-sitter 建 SQLite 索引，给 AI Agent 提供亚毫秒级代码结构查询

## 基本信息

| 字段 | 内容 |
|------|------|
| 仓库 | [colbymchenry/codegraph](https://github.com/colbymchenry/codegraph) |
| 语言/框架 | TypeScript (Node.js, tree-sitter, better-sqlite3) |
| 研究日期 | 2026-05-29 |
| 研究方式 | 源码阅读 + 文档分析 |
| 状态 | 🟢 已落地 |

## 核心思路

CodeGraph 定位很明确：**给 AI 编码 Agent 提供预建代码索引**。不是 IDE 插件，不是代码搜索工具，而是一个 MCP Server — 目的是让 Agent 在被问到"这个函数哪里被调用"、"X 怎么到达 Y"这类结构性问题时，不用自己去 grep+Read，而是直接问 CodeGraph，后者从预建的 SQLite 图里瞬间返回答案。

支持多种 AI Agent：Claude Code、Cursor、Codex CLI、OpenCode、**Hermes Agent**、Gemini CLI、Antigravity、Kiro。

基准测试（7 个真实仓库中位数）：工具调用次数减少 **57%**，Token 消耗减少 **51%**，成本降低 **18%**，速度提升 **16%**。大仓库（VS Code ~1 万文件）收益最明显：0 次文件 Read、0 次 grep、工具调用从 16 降到 5。

## 架构分析

```
文件 → ExtractionOrchestrator (tree-sitter) → SQLite DB (nodes/edges/files)
                   ↓
          ReferenceResolver (import匹配, 命名匹配, 框架模式)
                   ↓
          GraphQueryManager / GraphTraverser (调用者, 被调用者, 影响半径)
                   ↓
          ContextBuilder (Markdown/JSON → AI Agent)
                   ↓
          MCP Server
```

**节点类型（20种）**：file · module · class · struct · interface · trait · protocol · function · method · property · field · variable · constant · enum · enum_member · type_alias · namespace · parameter · import · export · route · component

**边类型（12种）**：contains · calls · imports · exports · extends · implements · references · type_of · returns · instantiates · overrides · decorates

**支持 24 种语言**：TypeScript · JavaScript · TSX · JSX · Python · Go · Rust · Java · C · C++ · C# · PHP · Ruby · Swift · Kotlin · Dart · Svelte · Vue · Liquid · Pascal · Scala · Lua · Luau · ObjC

**框架感知**：内置框架 Resolver 可识别 Express、Laravel、Rails、FastAPI、Django、Flask、Spring、Gin、Axum、ASP.NET、Vapor、React Router、SvelteKit、Vue/Nuxt、Cargo workspace 等框架的路由和模式，生成 `route` 节点和 `references` 边。

**持久化**：SQLite（better-sqlite3 原生模式优先，WASM 兜底），每项目独立 `.codegraph/` 目录。文件变更通过原生 FSEvents/inotify/RDCW 实时同步。

**MCP 工具（9个）**：

| 工具 | 作用 |
|------|------|
| `codegraph_context` | **主入口** — 传入任务描述，返回关联符号+源码，一次调用替代多次搜索 |
| `codegraph_trace` | 调用路径追踪 — "X 怎么到达 Y"，返回完整调用链（含动态分发桥接） |
| `codegraph_search` | 按名快速搜索符号 |
| `codegraph_callers` | 列出调用该符号的函数 |
| `codegraph_callees` | 列出该符号调用的函数 |
| `codegraph_impact` | 变更影响分析 — 改了这个会影响到谁 |
| `codegraph_node` | 单个符号详情（签名+位置+源码） |
| `codegraph_explore` | 批量查看多个相关符号的源码（替代多次 Read） |
| `codegraph_status` | 索引健康检查 |

## 关键发现

- **MCP Server Instructions 设计** — 在 MCP initialize 响应里发 Agent 指南（工具选择策略、常见链、反模式），这是我看过写得最好的 MCP tool guidance，比纯 tool JSON schema 描述好 10 倍
- **Project Cache 模式** — MCP handler 建 project cache 跨请求复用，支持跨项目查询
- **输出预算自适应** — 根据项目文件数动态调整 explore 输出上限，小项目用小预算避免上下文污染
- **Git 工作树兼容** — 启动时检测 git worktree vs index 不一致并告警
- **多层级解析** — AST 提取 (deterministic) → Import 解析 (文件级) → 命名匹配 (跨文件) → 框架模式 (框架级)，四层递进逐步精准
- **动态分发桥接** — 回调/闭包/React re-render 等动态跳转已纳入调用链追踪
- **与 Hermes Agent 深度集成** — 有专门的安装目标 (`src/installer/targets/hermes.ts`)，自动配置 `$HERMES_HOME/config.yaml` 的 `mcp_servers.codegraph` 和在 `platform_toolsets.cli` 中添加 `mcp-codegraph`

## 跟同类项目的对比

| 维度 | CodeGraph | 当前 Hermes 原生能力 |
|------|-----------|---------------------|
| 代码探索 | 预索引 SQLite（亚毫秒） | agent 自己 grep+Read（耗 Token） |
| 调用链追踪 | 自动图遍历返回完整路径 | 读源码手动追踪 |
| 动态分发 | 回调/闭包/React re-render 等动态跳转已桥接 | 不支持 |
| 框架感知 | 识别 Express/Django/Rails 等 20+ 框架路由 | 无 |
| 部署复杂度 | 每个项目需 `codegraph init -i` + 保持 MCP 服务运行 | 无需额外部署 |

## 可借鉴的点

1. **MCP 工具命名规范** — `codegraph_` 前缀 + 动词：`_context`（分析）、`_trace`（追踪）、`_search`（搜索）、`_explore`（浏览）、`_impact`（影响分析），清晰统一
2. **多层级解析管线** — AST → Import → 命名匹配 → 框架模式，逐层递进，精度逐步提升
3. **MCP Server Instructions** — 在协议层嵌入 Agent 使用指南，比纯 JSON schema 描述有效得多
4. **CSS 选择器式的符号查询** — `codegraph_context` 的设计思路值得学习：一次调用替代多次搜索
5. **收益分布洞察** — 核心价值不是省 Token，而是**减少 File Read 和 Grep 调用次数**——这是 Agent 工作流中最大的时间消耗和上下文污染源

## 决策

> **结论**：🟢 已落地

**为什么**：CodeGraph 直接解决了 AI Agent 在代码结构查询上的核心痛点——替代了低效的 grep+Read 循环。Hermes Agent 已有官方安装支持，配置简单，立即可用。基准测试显示工具调用减少 57%、Token 减少 51%，收益可量化。

**后续动作**：
- [ ] 确保已有项目都运行 `codegraph init -i` 完成索引
- [ ] 将 CodeGraph MCP 添加到 Hermes 默认配置中
- [ ] 在项目 onboarding 文档中加入 CodeGraph 索引步骤

**落地追踪**：
- 2026-05-29：首次分析
- 已通过 Hermes 安装目标自动集成到 `config.yaml`