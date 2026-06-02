# SCALE Engine — AI 编码工程治理 FSM 框架

> 让 AI 物理上做不到违规的事。6 阶段 FSM 状态机硬约束 + GateSystem 门禁 + 证据溯源，把工程治理从"prompt 让 AI 自觉"变成"代码让 AI 绕不过"。

## 基本信息

| 字段 | 内容 |
|------|------|
| 仓库 | Gitee: [hongmaple/scale-engine](https://gitee.com/hongmaple/scale-engine)（主库）/ GitHub: hongmaple/scale-engine |
| npm | `@hongmaple0820/scale-engine` |
| 版本 | v0.18.0（2026-05），8天10版，极速迭代 |
| 语言/框架 | TypeScript（~20 万行，含代码生成） |
| 研究日期 | 2026-05-19 |
| 研究方式 | 源码阅读 + 文档分析 |
| 状态 | ⚪ 待定 |

> **仓库**：https://gitee.com/hongmaple/scale-engine（主库）/ GitHub: hongmaple/scale-engine
> **npm**：`@hongmaple0820/scale-engine`
> **版本**：v0.18.0（2026-05），8天10版，极速迭代
> **调研日期**：2026-05-19

## 一句话定位

> 让 AI 物理上做不到违规的事。6 阶段 FSM 状态机硬约束 + GateSystem 门禁 + 证据溯源，把工程治理从"prompt 让 AI 自觉"变成"代码让 AI 绕不过"。

## 核心架构

### 6 阶段交付 FSM
```
定义 → 计划 → 构建 → 验证 → 评审 → 发布
(define) (plan) (build) (verify) (review) (ship)
```

### 11 种 Artifact 生命周期 DAG
```
Need → Insight → Spec → Plan → Task → Change
 → Evidence → Lesson/Defect → Release
```
每步都有 FSM 定义合法流转，不可跳过。

### 7 层安全模型
1. **FSM**：拦非法 Artifact 状态流转
2. **GateSystem**：build/lint/test/coverage/security 门禁
3. **EvidenceStore**：验证证据持久化
4. **ReviewAnalyzer**：确定性代码审查
5. **Detectors**：暴力重试拦截、过早完成检测、甩锅检测
6. **Ship 门禁**：阻截未审核文件
7. **OWASP 安全扫描**

## CLI 命令矩阵

| 类别 | 命令 |
|------|------|
| 治理初始化 | `scale init --governance-pack {standard/moe-workspace/go-service-matrix/...}` |
| 阶段工作流 | `scale define/plan/build/verify/review/ship` |
| 认知门控 | `scale context init/grill` · `scale diagnose plan` · `scale tdd slice` |
| 报告生成 | `scale artifact render/doctor/settle/open` |
| 自改进 | `scale evolution extract/improve/report/hooks` |
| MVP 模板 | `scale vibe --pack full-mvp` |
| 技能编排 | `scale skill repo/recommend/safety` |
| 工作区拓扑 | `scale workspace map` |
| 就绪检查 | `scale preflight/status` |

## 核心数据

- **~20 万行 TypeScript**（含代码生成）
- **16 个 Agent 平台适配器**：Claude Code、Codex CLI、OpenCode、Cursor、Gemini CLI、Trae、Hermes、Aider 等
- **12 个 Agent Profile**：前端/后端/测试/UI设计/运维/产品/代码审查/安全/数据库/性能/文档/架构
- **Governance Packs**：standard、project-scaffold、moe-workspace、resource-governance、go-service-matrix、node-library、frontend-app

## 自改进闭环（Evolution）

```
Defect → Lesson → Rule → Hook
```
- 阈值晋升：3次验证→规则，10次触发→提升，20次触发→Stop Hook
- 让团队经验沉淀为硬约束，而非反复写 prompt

## Hermes 对比

| 维度 | SCALE Engine | Hermes |
|------|-------------|--------|
| 治理层级 | 文件级 FSM 门禁（agent 物理上绕不过） | 任务级 Kanban 门禁（靠 agent 自觉） |
| 质量验证 | GateSystem + Evidence + Review + OWASP | 无 |
| 自改进 | Evolution 闭环（Defect→Lesson→Rule→Hook） | 无 |
| 部署 | CLI 工具，平台无关 | CLI + Gateway |
| 互补点 | 验证阶段可嵌入 Hermes kanban worker | 调度协调层可调 SCALE 做验证 |

**最值得借鉴的**：FSM 艺术状态机（而非简单跑测试）、Evolution 自改进闭环、Evidence 证据溯源

## 决策

> **结论**：⚪ 待定

**为什么**：SCALE Engine 的 FSM 硬约束治理理念与 Hermes 的 Kanban 任务级门禁形成互补——SCALE 提供文件级确定性门禁（AI 物理上绕不过），而 Hermes 提供任务级调度协调。其 Evolution 自改进闭环（Defect→Lesson→Rule→Hook）和 16 个 Agent 平台适配器（含 Hermes）表明已有直接可用的集成路径。需进一步评估治理边界和集成工作量。

**后续动作**：
- [ ] 评估 SCALE Engine 的构建/验证/评审门禁是否能嵌入 Hermes Kanban worker 作为质量验证阶段
- [ ] 调研 Evolution 自改进闭环的设计，看是否能在 Hermes 的 Hindsight 反思机制中引入类似的阈值晋升规则
- [ ] 试用 SCALE CLI，验证其对 Hermes 的适配器质量和集成体验
- [ ] 跟踪 SCALE Engine 的迭代速度（8天10版），评估稳定性

**落地追踪**：
- 2026-05-19：首次分析 SCALE Engine