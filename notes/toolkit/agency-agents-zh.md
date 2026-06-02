# agency-agents 中文版（AI 智能体专家团队）

- **状态**: 🟢 已落地
- **来源**: <https://github.com/jnMetaCode/agency-agents-zh>
- **上游**: <https://github.com/msitarzewski/agency-agents>

## 项目定位

一套**开箱即用的 AI 角色库**，将 215 个 AI 专家角色安装到 Hermes Agent 等 17 种主流 AI 编程工具中作为 skills。每个智能体都有明确的身份定义、关键规则、工作流程和交付物，而非通用提示词模板。

## 核心功能

1. **215 个 AI 专家角色** — 覆盖工程、设计、营销、产品、游戏、安全、金融等 18 个部门。其中 165 个来自英文原版翻译，50 个为中国市场原创（小红书/抖音/微信/B站运营、跨境电商、政务 ToG、医疗合规、Qt 工业上位机等垂直领域）。
2. **Hermes Agent 集成方式**：通过 `./scripts/convert.sh --tool hermes` 将每个智能体转换为 `SKILL.md` 格式，再通过 `./scripts/install.sh --tool hermes` 安装到 `~/.hermes/skills/` 目录下（全局生效）。可在 Hermes CLI 中用 `hermes skills` 查看管理，或在对话中自然语言激活。⚠️ 支持按分类选择性安装（如 `--category marketing`），避免全量安装造成性能开销。
3. **适用场景**：作为 skills 装载后，Hermes Agent 可在对话中按需调度不同专家角色，实现多领域 AI 协作。

## 分析结论

该仓库本质是一个**大规模 AI 角色 skill 包**，将 215 个垂直领域专家角色标准化为技能文件，使 Hermes Agent 能直接调用这些「领域专家」。50 个原创中文角色填补了国内平台运营和垂直行业场景的空白，对 Hermes 中文用户实用性高。项目落地状态良好，安装脚本完善，支持按需选择性安装。
