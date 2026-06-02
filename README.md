# 🔧 Workshop

> Where we take projects apart and learn how they work.
> 项目研究笔记 & Hermes Agent 自建工具集。

这个仓库收录了 **cookily** 在 AI Agent 生态中的外部项目研究笔记，以及从中提炼出的自建工具/技能。每次研究都会回答三个问题：

1. **这个项目是什么**（核心设计 + 架构分析）
2. **能借鉴什么**（可复用的思路 / 直接可用的技能）
3. **用上了吗**（落地决策 + 追踪）

---

## 目录

- [研究笔记（notes/）](#研究笔记) — 12 个项目的深度分析
- [自建工具（tools/）](#自建工具) — 分析后造出的 Hermes 技能/配置
- [谁适合看这个仓库](#谁适合看这个仓库)
- [格式规范](#格式规范)

---

## 研究笔记

| 项目 | 分类 | 一句话定位 | 状态 |
|------|------|-----------|:----:|
| [OpenHuman 🧠 → 路由思路已落地](./notes/agent/openhuman.md) | agent | 桌面助手 mascot 的三层模型路由架构 | 🟢 落地 |
| [agents-hive](./notes/agent/agents-hive.md) | agent | Go 多 Agent 底座，QC Plane + Worker 模式 | 🟡 留作参考 |
| [CodeGraph](./notes/engine/codegraph.md) | engine | 基于 MCP 的代码知识图谱服务 | 🟢 落地 |
| [PI](./notes/engine/pi.md) | engine | TypeScript Agent 终端编程工具库 | ⚪ 待定 |
| [SCALE Engine](./notes/engine/scale-engine.md) | engine | FSM 工程治理框架 | ⚪ 待定 |
| [Garden Skills 🌱 → 模板已吸收](./notes/integration/garden-skills.md) | integration | 4 个 Hermes 创意技能（图片/视频/UI） | 🟢 落地 |
| [Agency Agents ZH](./notes/toolkit/agency-agents-zh.md) | toolkit | 215 个 AI 专家角色，已安装到 Hermes | 🟢 落地 |
| [Superpowers ZH](./notes/toolkit/superpowers-zh.md) | toolkit | 20 个方法论 Skills，已安装到 Hermes | 🟢 落地 |
| [Agency Orchestrator](./notes/agent/agency-orchestrator.md) | agent | YAML 零代码多 Agent 协作引擎 | 🟢 落地 |
| [VSCode ACP](./notes/integration/vscode-acp.md) | integration | VSCode 的 ACP 协议插件 | ⚪ 待定 |
| [Hermes Skill Ideasphere](./notes/toolkit/hermes-skill-ideasphere.md) | toolkit | 抖音视频分析 + 剪辑流水线 | 🟡 留作参考 |

**状态说明：**
| 标记 | 含义 |
|:----:|------|
| 🟢 落地 | 分析结论已转化为实际动作（安装/改配置/吸收到 skill） |
| 🟡 留作参考 | 暂不采用，但记录设计思路以备后用 |
| ⚪ 待定 | 尚未决定，等待合适的时机或需求 |

> 📝 **所有已有研究已全部迁移完毕**，共 11 篇分析。

---

## 自建工具

> 点进 **[tools/](./tools/)** 看完整说明和部署步骤。

| 工具 | 来路 | 你需要它吗？ |
|------|------|-------------|
| **[multi-agent-dispatcher](./tools/skills/multi-agent-dispatcher/)** | agents-hive | 有多个 Agent Profile 需要隔离执行？ |
| **[routing-rules](./tools/configs/routing-rules.yaml)** | openhuman | 想让不同任务自动走不同模型？ |
| **[sketch-style-recipes](./tools/templates/sketch-style-recipes/)** | garden-skills | 做 HTML 原型想要 25 套现成风格？ |
| **[custom-provider-setup](./tools/skills/custom-provider-setup/)** | 实践总结 | 用非标准模型 Provider 需要配置辅助？ |
| **[apikey-image-gen-templates](./tools/templates/apikey-image-gen-templates/)** | garden-skills | 需要 94 套图片提示词模板？ |
| **[web-video-presentation](./tools/skills/web-video-presentation/)** | garden-skills | 想把文章做成视频风格的网页演示？ |
**[project-research-workflow](./tools/skills/project-research/)** | 多次实践 | 想让 AI 按标准化流程帮你研究项目？ |

---

## 谁适合看这个仓库

| 身份 | 能获得什么 |
|------|-----------|
| **cookily（作者）** | 快速回顾研究过的项目 + 直接部署自建工具 |
| **Hermes Agent 用户** | tools/ 目录下的技能可以直接复制到自己的环境中使用 |
| **路过的人** | notes/ 里的项目分析是纯知识分享，帮你了解 AI Agent 生态中的各种方案 |

---

## 格式规范

每篇研究笔记遵循 [TEMPLATE.md](./TEMPLATE.md) 格式：

```
# 项目名称
> 一句话定位（20字内）

## 基本信息  — 仓库、语言、研究日期、状态
## 核心思路  — 最核心的设计思想
## 架构分析  — 关键组件和关系
## 关键发现  — 源码/文档阅读中的重点
## 对比      — 与同类项目的差异
## 可借鉴点   — 值得带走的设计
## 决策      — 🟢/🟡/⚪ + 为什么 + 后续动作 + 落地追踪
```

---

## 贡献

这是 **cookily** 的个人学习仓库，不接受外部 PR。但欢迎通过 Issues 讨论项目分析内容。

---

<div align="center">
<i>Taking things apart since 2026.</i>
</div>