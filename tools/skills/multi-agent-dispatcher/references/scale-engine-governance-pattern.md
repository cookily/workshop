# SCALE Engine FSM 治理模式 — 多 Agent 架构的补充参考

SCALE Engine（v0.18.0, npm @hongmaple0820/scale-engine）的核心设计理念对多 Agent 协作架构有启发意义。

## 核心理念："让 AI 物理上做不到错的事"

不是说服 AI 自律，而是通过 FSM 状态机 + GateSystem 门禁 + EvidenceStore 证据溯源让 AI 绕不过去。

| 维度 | Hermes 的做法 | SCALE 的做法 | 能否借鉴 |
|------|--------------|--------------|---------|
| 任务边界 | Kanban 状态流转 + assignee 控制 | FSM 硬约束 + `process.exit(1)` 阻断 | 启发：子 agent 的 workspace 可以加更细粒度的门禁 |
| 质量验证 | 项目经理人工审核 | GateSystem 自动跑 build/lint/test/coverage/security | 可借鉴：kanban worker 完成前自动跑验证 |
| 证据溯源 | summary + kanban log | 命令输出 hash + 时间戳 + 文件 hash | 可借鉴：子 agent 产出物做哈希校验 |
| 自改进 | Hindsight 记忆（记忆用户偏好） | Defect→Lesson→Rule→Hook 阈值晋升 | 可借鉴：重复出现的缺陷自动升级为 kanban blocker |

## 对多 Agent 调度的启发

### 1. Agent 无关性

SCALE 的设计原则是**Headless 优先**——引擎不假设运行在哪个 Agent 里。Agent=客户端，引擎=服务端。这与 Hermes 多 Agent 调度架构的理念一致：主网关（调度层）和子 Agent（执行层）解耦。

### 2. 阶段化交付的标准通道

SCALE 定义了 6 阶段标准化交付：`define → plan → build → verify → review → ship`。

对应到多 Agent 协作：
- **define** → 项目经理拆解任务、写 body
- **plan** → 子 Agent 产出实施方案
- **build** → 子 Agent 执行
- **verify** → 自动验证（可集成 SCALE 的 verify gate）
- **review** → 代码审查（可集成 SCALE 的 review analyzer）
- **ship** → 项目经理审阅后 complete

### 3. 认知工作流门控

SCALE 的 `scale context`、`scale diagnose`、`scale tdd` 命令强制 Agent 在写代码前先做上下文理解和诊断。这解决了多 Agent 协作中常见的"子 Agent 拿到任务就盲目开干"的问题。

对应到 Hermes：可以在 sub-agent 的 SOUL.md 里嵌入类似规则——"拿到任务后先读相关文档，确认上下文，再开始执行"。

## 与 Hermes 的差异对比

| 方面 | SCALE Engine | Hermes Agent |
|------|-------------|--------------|
| 实现语言 | TypeScript | Python + Ink TUI |
| 平台适配 | 16个Agent平台（Claude Code, Codex, Hermes等） | 单一Agent平台 + 多Profile |
| 治理粒度 | 文件级（每个Artifact走FSM） | 任务级（Kanban状态流转） |
| 依赖 | 需`npm install -g`，项目内初始化 | 预装在服务器，开箱即用 |
| 迭代速度 | 8天10版（v0.10.0→v0.18.0） | 稳定版 |
| 社区 | GitHub + Gitee + npm + 文档站 | 开源社区 + 飞书群 |
| 设计哲学 | "让AI物理上做不到错的事" | "项目经理调度+专业Agent执行" |

## 参考

- SCALE Engine 源码：https://gitee.com/hongmaple/scale-engine
- 文档站：https://scale-os.hongmaple.top
- 本篇创建于 2026-05-19 深度学习产出