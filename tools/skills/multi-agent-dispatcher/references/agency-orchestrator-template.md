# agency-orchestrator 模板参考

## PACS可行性分析模板（实测可用）

路径：`/tmp/test-pacs.yaml`

```yaml
name: "PACS系统可行性分析"
description: "医院PACS系统市场、技术、竞品分析"

agents_dir: "/home/ubuntu/agency-agents-zh"

llm:
  provider: "claude-code"       # 用 claude-code，不用 hermes-cli
  model: "minimax/MiniMax-M2.7"  # 模型格式

concurrency: 2                   # 并行步骤数

inputs:
  - name: product_name
    required: true
  - name: target_market
    required: true

steps:
  - id: market_analysis
    role: "marketing/marketing-china-market-localization-strategist"
    task: |
      分析 {{product_name}} 在 {{target_market}} 的市场规模、竞争格局和进入壁垒。
      输出：市场规模数据、主要玩家、市占率分布、机会点。
    output: market_report

  - id: tech_analysis
    role: "engineering/engineering-software-architect"
    task: |
      分析 {{product_name}} 的核心技术架构选型、技术难点和实现路径。
      输出：技术栈建议、架构模式、关键挑战。
    output: tech_report

  - id: summary
    role: "sales/sales-deal-strategist"
    task: |
      综合以下分析，给出最终可行性结论：
      市场分析：{{market_report}}
      技术分析：{{tech_report}}
      输出格式：
      ## 结论：[✅ 可行 / ⚠️ 需谨慎 / ❌ 不可行]
      ## 市场评分（1-10）：X
      ## 技术评分（1-10）：X
      ## 风险点（Top3）
      ## 建议下一步
    depends_on: [market_analysis, tech_analysis]
```

## 执行命令

```bash
# 首次执行（串行，避免并发过高）
ao run /tmp/test-pacs.yaml \
  -i product_name="医院PACS系统" \
  -i target_market="二级医院" \
  --provider claude-code

# 查看输出
ls ~/ao-output/
cat ~/ao-output/PACS系统可行性分析-*/summary.md
```

## 关键教训

1. **provider 写死在 YAML 里**：`ao run --provider X` 无法覆盖 YAML 内的 provider 字段
2. **hermes-cli 不可用**：服务器无浏览器，OAuth 流程走不通
3. **输出在 ~/ao-output/**：不是命令执行的当前目录
4. **用 claude-code provider**：需提前在 Claude Code 配置 MiniMax 模型（`minimax/MiniMax-M2.7`）

## 其他可用内置模板

```bash
# 查看所有模板
ls /home/ubuntu/agency-orchestrator/workflows/

# 推荐：
# workflows/product-review.yaml       # 产品需求评审
# workflows/marketing/xiaohongshu-viral-post.yaml  # 小红书爆款笔记
# workflows/dev/pr-review.yaml         # PR三维度审查
# workflows/ops/incident-postmortem.yaml  # 事故复盘
```
