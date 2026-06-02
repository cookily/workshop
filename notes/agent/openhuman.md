# OpenHuman — 三层路由架构

> 桌面助手 mascot，三层路由（Provider → 本地/远程智能 → Agent hint）

## 基本信息

| 字段 | 内容 |
|------|------|
| 仓库 | [tinyhumansai/openhuman](https://github.com/tinyhumansai/openhuman) |
| 语言/框架 | Rust + Tauri v2 |
| 研究日期 | 2026-06-02 |
| 研究方式 | 源码阅读 |
| 状态 | 🟢 已落地 |

## 核心思路

OpenHuman 的核心路由思想是**让 Agent 自我感知任务类型并自动选择最优模型/Provider**，而非让用户手动选模型。全套三层路由体系从下到上分工明确：

1. **第一层**（Provider-level Router）—— 按 hint 分发到对应 Provider + Model
2. **第二层**（IntelligentRoutingProvider）—— 按任务复杂度在本地/远程之间智能决策，失败自动降级
3. **第三层**（Agent 发射 hint）—— Agent loop 在 spawn 子 agent 时自动携带 hint 标签

这套体系的核心创新在于：**Agent 根据当前任务类型自动发射 hint**（如 `hint:reasoning`、`hint:coding`），路由在 chat/completions 调用前完成，Agent 完全无感知。用户只需一个 OpenHuman 订阅，后端自动处理多 Provider 分发。

## 架构分析

```
┌─────────────────────────────────────────────────────────────────────┐
│  第三层：Agent 自动发射 hint                                        │
│                                                                     │
│  Agent Loop / 子 Agent                                              │
│    ├─ 前台对话 → hint:chat                                         │
│    ├─ 代码任务 → hint:coding                                       │
│    ├─ 深度推理 → hint:reasoning                                     │
│    ├─ 子 agent → hint:agentic                                       │
│    └─ 学习/反思 → hint:reasoning                                    │
│          │                                                          │
│          ▼                                                          │
├─────────────────────────────────────────────────────────────────────┤
│  第二层：IntelligentRoutingProvider（本地/远程智能路由）              │
│                                                                     │
│  classify() → TaskCategory                                          │
│    ├─ Lightweight: reaction, classify, format, sentiment → 本地优先  │
│    ├─ Medium: summarize, tool_lite → 看 RoutingHints                 │
│    └─ Heavy: reasoning, coding, agentic, chat → 强制远程             │
│                                                                     │
│  decide() → 路由决策                                                │
│    ├─ Privacy override → 强制本地，无 fallback                       │
│    ├─ Heavy → 强制远程                                              │
│    ├─ Lightweight + local healthy → 本地（远程 fallback）             │
│    ├─ Medium + latency Low / cost High → 本地（远程 fallback）        │
│    └─ Medium + no bias → 远程                                       │
│                                                                     │
│  quality check → should_fallback()                                   │
│    ├─ 输出 < 5 字符 → 降级                                          │
│    ├─ 输出含拒绝前缀 → 降级                                         │
│    └─ privacy_required 时禁止 fallback                              │
│          │                                                          │
│          ▼                                                          │
├─────────────────────────────────────────────────────────────────────┤
│  第一层：Provider-level Router（RouterProvider）                      │
│                                                                     │
│  resolve(model) → (provider_index, model)                           │
│    ├─ hint:xxx → route 表查（可动态增删 hint→provider 映射）          │
│    ├─ tier 名（reasoning-v1/agentic-v1/coding-v1）→ hint → route 表  │
│    └─ 不认识模型名 → 默认 provider 直发                              │
│                                                                     │
│  各 workload 独立 Provider 配置                                      │
│    chat_provider / reasoning_provider / coding_provider / ...        │
│    ├─ "cloud" → primary_cloud                                       │
│    ├─ "openai:<model>" → OpenAI                                     │
│    ├─ "anthropic:<model>" → Anthropic                               │
│    ├─ "ollama:<model>" → 本地 Ollama                                │
│    └─ "custom:<model>" → 自定义                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## 关键发现

- **发现 1：Agent 自我感知任务类型** — OpenHuman 的核心创新不是 UI 下拉选模型，而是 Agent loop 根据当前任务自动发射 hint。子 agent 通过 `ModelSpec::Hint("reasoning")` 指定 workload，路由完全透明。

- **发现 2：三层路由层层递进** — 第一层解决「去哪个 Provider」的问题，第二层解决「本地还是远程」的问题，第三层解决「当前是什么任务」的问题。三层互不耦合，可独立演化。

- **发现 3：质量降级的启发式检查** — `quality.rs` 只用了两个简单规则（< 5 字符 / 拒绝前缀匹配）就让本地降级决策非常可靠，不需要复杂模型。

- **发现 4：config.toml 的 workload 级 Provider 隔离** — 9 个独立 provider 字段覆盖了 Agent 所有可能的工作负载（chat/reasoning/agentic/coding/memory/embeddings/heartbeat/learning/subconscious），粒度很细。

- **发现 5：热加载能力** — `routes.rs` 的 ModelRouteConfig 支持运行时读 config，无需重启即可增减 hint→model 映射。Hermes 的 routing-rules.yaml 也支持热修改即时生效。

## 跟同类项目的对比

| 维度 | OpenHuman | Hermes（当前实现） |
|------|-----------|-------------------|
| **路由层级** | 上游，Provider 级 | 下游，Skill + delegate_task 级 |
| **任务类型感知** | ✅ Agent loop 自动发射 hint | ✅ routing-rules.yaml 声明式 task_type 匹配 |
| **多 Provider/多模型** | RouterProvider + workload provider 配置 | routing-rules.yaml 表 + 多 Profile |
| **路由表动态调整** | 运行时 config 热加载 | YAML 热修改即时生效 |
| **本地/远程自动路由** | IntelligentRoutingProvider + 降级检测 | ❌ 无（无本地模型需求） |
| **质量降级** | 本地失败自动降级远程 | delegate_task 失败 → 降级当前模型处理 |
| **健康检查** | Ollama health polling (30s TTL) | ❌ 无（无本地模型） |
| **路由 hint 机制** | privacy / latency / cost | task_type + indicators 匹配 |
| **Provider 路由表** | config.toml model_routes | routing-rules.yaml v2 |
| **无本地模型时行为** | 所有请求走远程 | 同 ✓ |

## 可借鉴的点

1. **Workload 级别 Provider 隔离** — OpenHuman 为 9 个 workload 提供独立 provider 字段。Hermes 已通过 routing-rules.yaml 的 task_type → {model, provider} 实现了类似能力，每个路由规则可指定独立 model 和 provider。

2. **Agent 自我感知任务类型** — OpenHuman 的 Agent loop 在 spawn 子 agent 时发射 hint。Hermes 自身就是「主 agent」，通过 routing-rules.yaml 的 indicators + 我（Hermes）手动分类实现相同效果。

3. **Fallback 链** — should_fallback() 的透明降级模式可直接复用于 delegate_task：第一次 delegate 失败 → 降级到当前模型直接处理。已在 Hermes 中实践。

4. **质量检查启发式** — quality.rs 的简单规则（<5 字符 = 低质量 / 拒绝前缀检测）可直接用于验证子 agent 输出，复杂度极低但效果显著。

5. **hint 发射模式** — 子 agent 的 context 中包含 hint 信息（如「你是资深技术架构师」），代替 OpenHuman 的 `hint:reasoning` 前缀。Hermes 的 routing-rules.yaml 中 `context` 字段承担了此角色。

## 决策

> **结论**：🟢 已落地

**为什么**：OpenHuman 的路由核心思路已经完整落地到 Hermes 的 routing-rules.yaml v2 中。具体对应：
- task_type（code/reasoning/research/vision/summarize/plan）→ 对应 OpenHuman 的 hint 机制
- model + provider 字段 → 对应 OpenHuman 的 RouterProvider resolve() 能力
- indicators 匹配 → 替代 OpenHuman 的 Agent loop 自动发射 hint（Hermes 手动分类更直接）
- context 字段 → 对应 OpenHuman 的 hint 命名体系（替代 `hint:reasoning` 前缀传参模式）

**后续动作**：
- 无（已落地）

**落地追踪**：
- 2026-05-22：首次分析 OpenHuman 路由架构
- 2026-05-25：产出详细源码分析文档（.hermes/skills/llm-dynamic-routing/references/）
- 2026-06-02：路由思路落地至 routing-rules.yaml v2，task_type + model + provider 方案投入使用