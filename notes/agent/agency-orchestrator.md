# Agency Orchestrator

> YAML 零代码多 AI 角色自动协作引擎，一句话出方案。

## 基本信息

| 字段 | 内容 |
|------|------|
| 仓库 | [jnMetaCode/agency-orchestrator](https://github.com/jnMetaCode/agency-orchestrator) |
| 语言/框架 | TypeScript (npm) |
| 研究日期 | 2026-05-22 |
| 研究方式 | 源码阅读 + 实际部署 |
| 状态 | 🟢 已落地 |

## 核心思路

用户只需要说一句话，系统自动拆解任务 → 从 211 个预置角色中匹配 → 生成 DAG 工作流 → 并行执行 → 输出完整方案。

和 CrewAI/LangGraph 的**本质区别**：后者需要开发者写 Python 代码定义 Agent 和图结构，而 Agency Orchestrator 完全零代码——用户只需一句话或一个 YAML 文件。

## 架构分析

```
用户一句话 (ao compose "...")
       │
       ▼ ┌──────────────────┐
       │  Task Decomposer   │ ← LLM 自动拆解任务
       └─┬──────────────────┘
         │
         ▼ ┌──────────────────┐
         │  Role Matcher      │ ← 从 211 角色中自动匹配
         └─┬──────────────────┘
           │
           ▼ ┌──────────────────┐
           │  DAG Builder       │ ← 检测依赖，生成执行图
           └─┬──────────────────┘
             │
       ┌─────┴─────┐
       │  并发执行   │ ← 多角色并行，自动传变量
       └─────┬─────┘
             │
             ▼ ┌──────────────────┐
             │  Results Aggregator│ ← 汇总至最终输出
             └───────────────────┘
```

### 核心能力

- **DAG 自动检测** — 不需要手动建图，系统自动识别 step 间的变量依赖
- **条件分支** — `condition` 字段支持 `{{var}} contains X` 语法
- **循环迭代** — `loop` 字段支持自动重试，最多 N 次，满足条件退出
- **Resume 断点续跑** — `--resume last --from <step-id>` 只重新执行指定步骤及下游
- **7 种免 API Key 方式** — 内置免费模型通道
- **10 种大模型支持** — Claude、DeepSeek、OpenAI、Ollama 等

## 关键发现

1. **与 agency-agents-zh 天然耦合** — 角色库直接复用 agency-agents-zh 的 211 个角色文件
2. **YAML 是关键抽象** — 把 Multi-Agent 协作降维成 YAML 配置，门槛极低
3. **Resume 机制设计巧妙** — 每次运行保存所有中间输出到 `ao-output/`，支持精准迭代
4. **CLAUDE.md 规范** — 项目自带 CLAUDE.md 说明 worklow 的迭代使用方式，体现了 AI-first 设计

## 与同类项目的对比

| 维度 | Agency Orchestrator | CrewAI / LangGraph |
|------|-------------------|-------------------|
| 使用方式 | 一句话 / YAML | 写 Python 代码 |
| 角色数 | 211 个预置 | 自己定义 |
| 并行调度 | DAG 自动检测 | 手动建图 |
| 安装依赖 | npm + 2 个依赖 | pip + 几十个包 |
| 断点续跑 | 原生支持 | 需自行实现 |
| 中文支持 | 全部角色中文 | 英文为主 |

## 可借鉴的点

- **"一句话"入口** — 把复杂配置简化为自然语言，是降低门槛的关键
- **YAML 作为编排语言** — 比 Python DSL 更直观，可读性更高
- **角色复用** — agency-agents-zh 的角色库是一次性投入，后续所有 workflow 自动受益
- **迭代优先** — Resume 机制设计让用户可以先跑通再精调，而不是一次性追求完美

## 决策

> **结论**：🟢 已落地

**为什么**：已通过 npm install 全局安装到服务器，`ao` 命令可用。Hermes orchestrate 功能可以对接使用。

**后续动作**：
- [x] 2026-05-22：npm install -g agency-orchestrator 安装
- [ ] 与 Hermes 工作流深度集成（利用 resume 做迭代式任务执行）