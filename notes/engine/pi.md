# Pi Agent Harness — TypeScript 编码 Agent Monorepo

> TypeScript 编码 Agent 框架，与 Claude Code / Codex 同赛道。5 个 npm 包，自带多 Provider LLM API + Agent Runtime + TUI + Web UI。

## 基本信息

| 字段 | 内容 |
|------|------|
| 仓库 | [earendil-works/pi](https://github.com/earendil-works/pi)（活跃维护中） |
| 官网 | https://pi.dev |
| 许可 | MIT |
| 语言/框架 | TypeScript (Monorepo, 5 npm 包) |
| 研究日期 | 2026-05-19 |
| 研究方式 | 源码阅读 + 文档分析 |
| 状态 | ⚪ 待定 |

> **仓库**：https://github.com/earendil-works/pi（活跃维护中）
> **官网**：https://pi.dev
> **许可**：MIT
> **调研日期**：2026-05-19

## 一句话定位
> TypeScript 编码 Agent 框架，与 Claude Code / Codex 同赛道。5 个 npm 包，自带多 Provider LLM API + Agent Runtime + TUI + Web UI。

## 5 个包

| 包（@earendil-works/） | 功能 |
|------------------------|------|
| pi-ai | 统一多 Provider LLM API（OpenAI/Anthropic/Google 等） |
| pi-agent-core | Agent Runtime + 工具调用 + 状态管理 |
| pi-coding-agent | 交互式编码 Agent CLI（带 TUI） |
| pi-tui | 终端 UI 渲染库（差分渲染） |
| pi-web-ui | AI 聊天 Web 组件 |

## 亮点

### Session Sharing
- 工具 `pi-share-hf` 把 Agent 工作会话上传到 Hugging Face
- 公开 benchmark，作者 badlogicgames 持续公开自己的 sessions
- 口号："真正世界任务的失败模式比玩具 benchmark 更有价值"

### 严格质量门禁
- AGENTS.md 11K+ 字开发规则
- 新贡献者 PR/Issue 自动关闭（每日人工审核）
- 规则包括：不许 inline import、不许 any、不许硬编码 keybinding、不许保留废弃兼容性代码

### 活跃度
- 2026-05-19 刚 git pull 回 951 行变更
- 新的 provider 不断加入（AWS Bedrock Converse Stream 等）
- 社区活跃（Discord）

## 跟我们的关系
- 与 Hermes 同赛道但更重 TUI 体验
- Session sharing 理念值得借鉴（Hermes 的 Kanban + Hindsight 已有类似能力但无公开共享机制）
- AGENTS.md 的严格程度值得学习（我们的 multi-agent-dispatcher skill 可以吸收部分规则）

## 决策

> **结论**：⚪ 待定

**为什么**：Pi Agent Harness 与 Hermes 同属 Agent 框架赛道，其 Session Sharing 机制（公开失败模式到 Hugging Face）和严格质量门禁（AGENTS.md 规则体系）有独特价值。需要进一步评估具体哪些能力可以引入 Hermes，以及是否存在直接集成或合作的必要。

**后续动作**：
- [ ] 评估 Pi 的 AGENTS.md 规则体系，将适用的开发规则吸收到 Hermes 的 multi-agent-dispatcher skill 中
- [ ] 调研 Session Sharing 机制是否值得在 Hermes Kanban + Hindsight 基础上实现公开共享功能
- [ ] 跟踪 Pi 的发展动态，评估长期集成或合作的可能性

**落地追踪**：
- 2026-05-19：首次分析 Pi Agent Harness