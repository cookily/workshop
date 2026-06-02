# Garden Skills 调研分析 & 整合落地报告

**最后更新**: 2026-06-02

---

## 项目概览

| 属性 | 值 |
|------|-----|
| GitHub | https://github.com/ConardLi/garden-skills |
| Stars / Forks | 6,600+ / 915+（2026-05-29 数据） |
| 许可证 | MIT |
| 最新提交 | 2026-05-29（非常活跃） |
| 兼容 Agent | Claude Code、Claude.ai Web、Cursor、Codex CLI、Gemini CLI、OpenCode |
| 安装方式 | `npx skills` CLI、Claude Code 插件市场、Release ZIP、Git Submodule、手动拷贝 |

**一句话总结**: ConardLi 维护的 Agent Skills 精选集合，目前 4 个生产级 Skill，面向 AI 编程助手，用 SKILL.md 格式包装成插件化、可安装的能力模块。

---

## 4 个 Skill 详解

### 1. web-design-engineer（设计 / 前端）

- **定位**: 把 AI 生成的网页从"能用"提升到"惊艳"
- **核心**: 6 步设计工作流（需求 → 上下文 → 设计系统 → v0 → 全量构建 → 验证）
- **亮点**: 25 种风格配方（Linear、Aesop、Pentagram、Bloomberg、Stripe Press、Mid-Century 等），每种含具体调色盘、字体、签名动作、反模式
- **规格**: SKILL.md 33K，README 27K，含 references/ 子目录
- **适合**: 落地页、仪表盘、交互原型、HTML 幻灯片、UI 模型

### 2. web-video-presentation（Web 视频 / 演示）

- **定位**: 把脚本/文章/教程/产品演示转换成 16:9 Web 演示，可录屏为视频
- **核心**: Vite + React + TypeScript 脚手架，章节/步骤游标驱动
- **亮点**: 23 套内置主题、可插拔 TTS（内置 MiniMax + OpenAI，预留 ElevenLabs/edge-tts 占位符）
- **规格**: 有完整的 templates/、themes/、scripts/、references/ 子目录
- **适合**: 知识科普视频、产品演示、技术讲座

### 3. gpt-image-2（图像生成 / 提示词工程）

- **定位**: 面向 GPT Image 2 和兼容 API 的图片生成 Skill
- **核心**: 三种运行时模式（本地 Garden / 宿主原生 / 仅顾问写提示词）
- **亮点**: 18 个视觉品类、79 个结构化提示词模板（references/ 下）
- **规格**: SKILL.md 26K，references/ 下 19 个子目录
- **适合**: 海报、UI 模型、产品视觉、信息图、教学图表、漫画

### 4. kb-retriever（本地知识库检索）

- **定位**: 从本地 knowledge/ 目录检索结构化文档
- **核心**: 分层索引 → 渐进搜索 → PDF/Excel 学习后再处理
- **亮点**: 限定最多 5 轮搜索防失控，支持 grep/pdftotext/pdfplumber/pandas
- **规格**: SKILL.md 14K
- **适合**: 基于本地文档库的问答、技术规范检索

---

## 与现有能力对比

| 维度 | Garden Skills | 我们的 Skills（Hermes） |
|------|--------------|----------------------|
| 设计 Web 页面 | ✅ web-design-engineer（25 种风格配方） | ✅ `sketch`、`popular-web-designs`、`architecture-diagram` |
| Web 视频/演示 | ✅ web-video-presentation（23 主题 + TTS） | ✅ `sketch` 做原型，已直接吸收 |
| 图片生成 | ✅ gpt-image-2（79 模板） | ✅ `apikey-image-gen`、`comfyui`，已吸收模板 |
| 本地知识检索 | ✅ kb-retriever（层次索引 + 渐进搜索） | ✅ Hermes 自身 hindsight 记忆检索 |
| Skill 生态/安装 | ✅ `npx skills` 标准 CLI，插件市场，Release ZIP | Hermes 有 `skill_manage`/`hermes skills`，格式相同（SKILL.md） |
| 多 Agent 兼容 | ✅ Claude Code/Cursor/Codex/Gemini/OpenCode | 主要针对 Hermes Agent 生态 |

---

## 🟢 吸收落地状态

Garden Skills 的模板已被吸收到以下 3 个 Hermes Skill，**状态 🟢 已落地**：

| Garden Skills 源 | 吸收到 Hermes Skill | 吸收内容 | 状态 |
|:-----------------|:-------------------|:---------|:----:|
| `gpt-image-2` | `apikey-image-gen` | 79 个结构化提示词模板、18 个视觉品类分类体系、Mode 检测 + 三种运行时模式 | 🟢 |
| `web-design-engineer` | `sketch` | 25 种风格配方、6 步设计工作流、反 AI 俗套清单、设计方向顾问方法论 | 🟢 |
| `web-video-presentation` | `web-video-presentation` | 23 套主题架构、Vite + React + TypeScript 脚手架、可插拔 TTS 集成方案 | 🟢 |

> `kb-retriever` 做参考但未被直接吸收 — Hermes 有 hindsight 语义搜索能力，暂不重现分层索引。

---

## 价值提炼

### 1. 设计风格配方 —— `web-design-engineer` → `sketch`

每个配方包含：
- 具体的调色盘（`oklch()` 色彩空间）
- 字体栈（含后备方案）
- 签名动作（signature moves）
- 反模式清单（避免千篇一律的生成式 UI）
- 适用场景标签

这套方法论极大提升了设计输出的质量下限。

### 2. 演示/录播视频 —— `web-video-presentation`

填补了生态缺口。核心架构：
```
固定 1920×1080 舞台 → 按视口缩放 → (chapter, step) 游标驱动
→ 硬 checkpoint（稿子/主题/outline/开发模式/音频）
→ 可插拔 TTS 合约（三函数契约）
→ 23 主题（编辑/终端/工程/瑞士国际主义等）
```

23 套主题一览（部分）：
- `creative-voltage` — 创意分享
- `blueprint` — 技术架构
- `swiss-ikb` — 数据汇报
- `chalk-garden` — 科普讲解
- + 19 套更多主题，每套独立设计签名

可插拔 TTS 架构：
- 内置 2 个 provider：MiniMax `mmx-cli` + OpenAI TTS via curl
- 预留现成代码片段：ElevenLabs / edge-tts / Azure / Google Cloud / macOS `say`

### 3. 图片生成提示词模板 —— `gpt-image-2` → `apikey-image-gen`

18 个视觉品类、79 个模板，覆盖：
- academic-figures（学术图：graphical-abstract, neural-network-architecture...）
- ui-mockups（UI 样机：chat-interface-scene, live-commerce-ui...）
- infographics（信息图：bento-grid-infographic, comparison-infographic...）
- technical-diagrams（技术架构图：system-architecture...）
- branding-and-packaging（品牌包装：mascot-brand-kit, cosmetic-packaging...）
- storyboards-and-sequences（分镜：anime-key-visual...）
- maps（地图：food-map, travel-route-map...）
- + 11 个更多品类

三种运行时模式：
- **Mode A**: Garden 本地生图
- **Mode B**: 委托宿主原生图像工具
- **Mode C**: 纯提示词顾问（退化模式）

---

## 项目架构参考（多 Skill Monorepo 最佳实践）

### 目录结构

```
garden-skills/
├── skills/                     # 所有 Skill 集合
│   ├── web-video-presentation/ # Skill 1
│   │   ├── SKILL.md            # Agent 指令（必需）
│   │   ├── README.md           # 人类文档
│   │   ├── references/         # 扩展参考（按需加载）
│   │   ├── scripts/            # 可执行工具
│   │   ├── templates/          # 脚手架模板
│   │   └── themes/             # 主题系统
│   ├── web-design-engineer/    # Skill 2
│   │   └── ...
│   ├── gpt-image-2/            # Skill 3
│   │   └── ...
│   └── kb-retriever/           # Skill 4
│       └── ...
├── .claude-plugin/
│   └── marketplace.json        # 插件包定义
├── scripts/release/            # 发版工具链
├── demo/                       # 演示项目
├── website/                    # 示例网站
└── dist/prompt/                # 参考提示词
```

### 插件市场包定义

```json
{
  "presentation-skills":  ["web-video-presentation"],
  "web-design-skills":    ["web-design-engineer"],
  "knowledge-base-skills": ["kb-retriever"],
  "image-generation-skills": ["gpt-image-2"]
}
```

### Skill 结构规范

每个 Skill 遵循标准格式：

```
<skill-name>/
├── SKILL.md       ← 必需：YAML frontmatter + Agent 指令
├── README.md      ← 人类文档
├── references/    ← 可选：按需加载的扩展文档
├── scripts/       ← 可选：确定性可执行代码
└── assets/        ← 可选：模板、字体、图标
```

Agent 根据 `SKILL.md` 的 frontmatter 里的 `description` 决定是否激活该 Skill。

---

## 关键发现

1. **`web-design-engineer` 的 25 种风格配方非常有价值** → ✅ 已吸收到 `sketch`
2. **`web-video-presentation` 填补了生态缺口** → ✅ 已直接落地同名 skill
3. **`kb-retriever` 的分层检索思路值得参考** → 暂未吸收，Hermes 有 hindsight 语义搜索
4. **项目本身是 Skill 交付的最佳实践模板**：
   - 完整的 CI/CD 管线（release 脚本、README 自动同步、SHA-256 校验）
   - 多语言文档（中英日）
   - 多安装方式（CLI / 插件市场 / ZIP / submodule / 手动）
   - 清晰的技能清单和版本管理
   - manifest.json 元数据标准化

---

## 能做什么 / 不能做什么

| 能 | 不能 |
|----|------|
| 生成精美网页原型（25 种设计风格） | 不能直接集成到后端（纯前端 Skill） |
| 制作可录屏的 16:9 知识视频演示 | 不能替代专业视频剪辑工具（动效有限） |
| 调用 GPT Image 2 API 出图（79 种提示模板） | 不能调用非 OpenAI 兼容的图像 API |
| 从本地知识库分层检索 Markdown/PDF/Excel | 不支持数据库 / 网络 API 检索 |
| 用 npx skills 一键安装到多个 Agent | 部分 Skill 依赖外部 API key（如 GPT Image 2） |

---

## 安装方式速查

| # | 方式 | 命令 | 适合场景 | 能钉版本？ |
|---|------|------|---------|:---------:|
| A | `skills` CLI（npx） | `npx skills add ConardLi/garden-skills -s <name>` | 任意 Agent，一键安装 | ✅ via tag URL |
| B | Claude Code 插件市场 | `/plugin install <pack>@garden-skills` | Claude Code 用户 | ✅ 市场版本 |
| C | Release ZIP | `curl + unzip` | CI / 内网 | ✅ ✅ 不可变 |
| D | 手动拷贝 | `git clone + cp` | 本地魔改 | ❌ |
| E | Git Submodule | `git submodule add` | 嵌入大项目 | ✅ via SHA |

---

## 参考链接

- GitHub 仓库: https://github.com/ConardLi/garden-skills
- 线上案例站（gpt-image-2）: https://gpt-image2.mmh1.top（160+ 案例展示）
- Agent Skills 规范: https://agentskills.io
- Anthropic 参考仓库: https://github.com/anthropics/skills
