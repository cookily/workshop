# 自建工具集

这些是从项目研究中直接产出的东西。每个工具都标注了"你需要它吗"——扫一眼就能判断要不要用。

---

## 总览

| 工具 | 来路 | 类型 | 部署难度 |
|------|------|------|---------|
| [server-guardian](#server-guardian) | 原创 | Python 项目 | ★☆☆ |
| [multi-agent-dispatcher](#multi-agent-dispatcher) | agents-hive | Hermes Skill | ★☆☆ |
| [routing-rules](#routing-rules) | openhuman | 配置文件 | ★☆☆ |
| [sketch-style-recipes](#sketch-style-recipes) | garden-skills | 模板配方 | ★☆☆ |
| [custom-provider-setup](#custom-provider-setup) | 实践总结 | Hermes Skill | ★☆☆ |
| [apikey-image-gen-templates](#apikey-image-gen-templates) | garden-skills | 模板配方 | ★☆☆ |
| [web-video-presentation](#web-video-presentation) | garden-skills | Hermes Skill | ★☆☆ |
| [project-research-workflow](#project-research-workflow) | 多次实践总结 | Hermes Skill | ★☆☆ |

---

## multi-agent-dispatcher

**你需要它吗？** 如果你同时管理多条独立任务线（比如医院项目的调研 Agent 和副业的开发 Agent 同时跑），这个 skill 让 Hermes 自动分流给不同 Profile 执行，互不干扰、记忆隔离。

**怎么装？**
```bash
# 复制 skill 到本地
cp -r skills/multi-agent-dispatcher/ ~/.hermes/skills/devops/
# 确认加载
hermes skills list | grep multi-agent
```

**配置依赖：** 需要先配置好对应的 Profile（`hospital`, `side-project`），每个 Profile 有独立 Hindsight 银行做记忆隔离。

**来路** → [notes/agent/agents-hive.md](../notes/agent/agents-hive.md) — 受 Go 多 Agent 底座启发，简化成一个纯 Hermes 生态的 skill。

---

## server-guardian

**你需要它吗？** 如果你有一台 Linux 服务器跑着多个服务（Nginx、Docker、自定义进程），需要一个自动化健康检查+飞书告警+日报的系统——而不是每天早上 ssh 上去一个个看。特别适合有飞书/钉钉的企业或个人开发者。

**它能干嘛？**
- CPU/内存/磁盘/Swap/负载监控
- 进程+端口检查（你配什么它就查什么）
- SQLite 看板 DB 完整性检查
- 看板备份时效性检查
- 分级告警（Critical/Warning/Info）推送飞书
- 每日健康日报自动生成
- 历史数据 SQLite 存储，支持趋势查询

**怎么装？**
```bash
# 安装依赖
pip install pyyaml

# 跑一次看看效果
cd tools/server-guardian/
python3 main.py

# 持续监控（后台）
python3 main.py --daemon &

# 看日报
python3 main.py --report
```

**相关文件：**
- `server-guardian/main.py` — CLI 入口（~194 行）
- `server-guardian/core/checkers.py` — 各检查函数（~319 行）
- `server-guardian/core/collector.py` — 采集调度（~214 行）
- `server-guardian/core/evaluator.py` — 告警评估（~224 行）
- `server-guardian/alert/feishu.py` — 飞书推送（~148 行）
- `server-guardian/storage/db.py` — SQLite 存储（~165 行）
- `server-guardian/report/daily.py` — 日报生成（~119 行）
- `server-guardian/config.yaml` — 阈值+监控项配置

---

## routing-rules

**你需要它吗？** 如果你的 Hermes 配置了多个模型 Provider，想把写代码、查资料、深度推理等任务自动走不同模型（比如写代码走 Claude Code、查资料走 Flash、推理走 Pro），不用手切。

**怎么装？**
```bash
# 复制配置
cp configs/routing-rules.yaml ~/.hermes/routing-rules.yaml
# 重启网关
sudo systemctl restart hermes-gateway
```

**配置依赖：** 需要 Hermes Agent v0.6+ 支持 LLM Dynamic Routing。

**来路** → [notes/agent/openhuman.md](../notes/agent/openhuman.md) — 受 OpenHuman 三层路由分类思路启发，简化成 7 种任务类型。

---

## sketch-style-recipes

**你需要它吗？** 你经常用 Hermes 做 HTML 原型/设计稿，但每次风格都要从零调 CSS。这里有 25 套现成的视觉风格（毛玻璃、极简、赛博朋克、新拟态...），直接套。

**怎么装？**
```bash
# 复制到 sketch skill 的引用目录
cp -r tools/sketch-style-recipes/ ~/.hermes/skills/creative/sketch/references/style-recipes/
```

**来路** → [notes/integration/garden-skills.md](../notes/integration/garden-skills.md) — 从 garden-skills 的 web-design-engineer 25 种风格配方中吸收。

---

## custom-provider-setup

**你需要它吗？** 你在用非 OpenAI 标准的模型 Provider（商汤 SenseNova、MiniMax 等），需要配置 vision 辅助模型、自定义 Header、或者同时管理多个模型的 role 分工。

**怎么装？**
```bash
cp -r skills/custom-provider-setup/ ~/.hermes/skills/mlops/
```

**内容：** 含三模型 API 规格对比表、vision auxiliary 配法、VLM vs T2I 区分说明、自定义 Header 注入方案。

---

## apikey-image-gen-templates

**你需要它吗？** 你经常用 Hermes 生成图片，需要各种风格的提示词模板（3D 渲染、水墨画、产品摄影、像素艺术...），覆盖 18 个品类 94 套。

**怎么装？**
```bash
cp -r tools/apikey-image-gen-templates/ ~/.hermes/skills/creative/apikey-image-gen/references/
```

**来路** → [notes/integration/garden-skills.md](../notes/integration/garden-skills.md)

---

## web-video-presentation

**你需要它吗？** 你有一篇文章或口播稿，想把它做成"看起来像视频"的网页演示（16:9 全屏、逐段展示、自动播放），还能合成口播音频。

**怎么装？** 这是 Hermes 内置 skill，无需安装。直接在对话中要求"把这篇文章做成网页视频演示"就会自动调用。

**来路** → 吸收自 garden-skills 的视频展示方案。

---

## project-research-workflow

**你需要它吗？** 你经常丢项目链接给我（Hermes）分析，想要一个标准化的研究流程：建看板 → 克隆 → 读源码 → 写分析 → 评估吸收 → 归档。

**怎么装？**
```bash
cp -r skills/project-research/ ~/.hermes/skills/research/
```

**提醒：** 这个 repo 本身（workshop）就是这个 workflow 的输出目的地——每次研究完的分析应该放到 `notes/` 目录下。

