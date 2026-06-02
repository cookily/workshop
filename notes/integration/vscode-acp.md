# VS Code ACP Client — VSCode 的 ACP 协议客户端插件

**最后更新**: 2026-06-02

---

## 项目概览

| 属性 | 值 |
|------|-----|
| GitHub | https://github.com/formulahendry/vscode-acp |
| 许可证 | MIT |
| 作者 | formulahendry |
| 安装 | [VS Code Marketplace](https://marketplace.visualstudio.com/items?itemName=formulahendry.acp-client) / [Open VSX](https://open-vsx.org/extension/formulahendry/acp-client) |
| 快捷键 | `Ctrl+Shift+A` 打开聊天面板 |
| 前置依赖 | Node.js 18+、ACP 兼容的 Agent（本地或 npx） |

**一句话总结**: 在 VS Code 中连接任意 ACP 兼容 AI 编码助手的官方客户端插件，支持多 Agent、会话管理、MCP 文件系统/终端、权限控制。

---

## 预配置的 11 个 Agent

| Agent | 启动命令 |
|-------|---------|
| GitHub Copilot | `npx @github/copilot-language-server@latest --acp` |
| Claude Code | `npx @agentclientprotocol/claude-agent-acp@latest` |
| Gemini CLI | `npx @google/gemini-cli@latest --experimental-acp` |
| Qwen Code | `npx @qwen-code/qwen-code@latest --acp --experimental-skills` |
| Auggie CLI | `npx @augmentcode/auggie@latest --acp` |
| Qoder CLI | `npx @qoder-ai/qodercli@latest --acp` |
| Codex CLI | `npx @zed-industries/codex-acp@latest` |
| OpenCode | `npx opencode-ai@latest acp` |
| OpenClaw | `npx openclaw acp` |
| Kiro CLI | `kiro-cli acp` |
| **Hermes Agent** | `hermes acp` |

> Hermes Agent 是 Python 包，需通过 pip 安装，确保 `hermes` 在 PATH 上并从同一 shell/venv 启动 VS Code。

---

## 核心功能

- **多 Agent 支持**: 内置 11 个预配置 Agent，可自由添加自定义 Agent
- **单 Agent 聚焦**: 同一时间一个 Agent 活跃，无缝切换
- **会话管理**: 每个 Agent 可展开查看历史会话，支持 `session/list` 协议或本地缓存
- **会话配置选项**: 动态渲染 Agent 广告的模式/模型/推理等级选择器
- **交互式聊天**: 内嵌聊天面板，支持 Markdown、内联工具调用显示、可折叠工具区
- **思考过程展示**: 可折叠推理展示块，带流式动画和耗时显示
- **Slash 命令**: 自动补全弹出，支持键盘导航
- **文件系统集成**: Agent 可读写工作区文件（MCP）
- **终端执行**: Agent 可运行命令，实时显示终端输出
- **权限管理**: 可配置自动审批策略（`ask` / `allowAll`）
- **协议流量日志**: 检查所有 ACP JSON-RPC 消息（请求/响应/通知）
- **Agent 注册表**: 浏览发现可用 ACP Agent
- **聊天持久化**: 切换面板后会话保留

---

## 设置项

| 设置 | 默认值 | 说明 |
|------|--------|------|
| `acp.agents` | 11 个 Agent | Agent 配置，含 `command`、`args`、`env` |
| `acp.autoApprovePermissions` | `ask` | 权限请求处理：`ask` 询问 / `allowAll` 自动允许 |
| `acp.defaultWorkingDirectory` | `""` | 默认工作目录，空则用当前工作区 |
| `acp.logTraffic` | `true` | 将 ACP 协议流量记录到 ACP Traffic 输出通道 |

---

## 命令清单

| 命令 | 说明 |
|------|------|
| `ACP: Connect to Agent` | 连接 Agent |
| `ACP: New Conversation` | 新建对话 |
| `ACP: Send Prompt` | 发送消息 |
| `ACP: Cancel Current Turn` | 取消当前轮次 |
| `ACP: Disconnect Agent` | 断开连接 |
| `ACP: Restart Agent` | 重启 Agent 进程 |
| `ACP: Open Chat Panel` | 聚焦聊天面板 |
| `ACP: Add Agent Configuration` | 添加 Agent 配置 |
| `ACP: Remove Agent` | 移除 Agent |
| `ACP: Set Agent Mode` | 设置运行模式 |
| `ACP: Set Agent Model` | 设置模型 |
| `ACP: Refresh Sessions` | 刷新会话列表 |
| `ACP: Show Log` | 打开日志通道 |
| `ACP: Show Protocol Traffic` | 打开协议流量通道 |
| `ACP: Browse Agent Registry` | 浏览 Agent 注册表 |

---

## 架构

```
Core: AgentManager → ConnectionManager → SessionManager → AcpClientImpl
         ↕                    ↕
    FileSystemHandler    TerminalHandler
    PermissionHandler    SessionUpdateHandler

UI:  SessionTreeProvider / ChatWebviewProvider / StatusBarManager
Config: AgentConfig / RegistryClient
Utils: Logger / StreamAdapter
```

Agent 通信使用 ACP 协议（JSON-RPC 2.0 over stdio）。

---

## 开发 & 构建

```bash
git clone https://github.com/formulahendry/vscode-acp.git
cd vscode-acp
npm install
npm run compile    # 构建
npm run watch      # 开发监听模式
npm test           # 测试
npx @vscode/vsce package   # 打包 .vsix
```

前置条件: Node.js 18+、VS Code 1.85+。

按 `F5` 启动 Extension Development Host 进行调试。

---

## Known Issues

- Agent 必须在系统 PATH 或 `npx` 可访问
- 部分 Agent 需要额外认证
- 附件上传功能尚未实现

---

## 相关项目

- [ACP UI](https://github.com/formulahendry/acp-ui) — 跨平台桌面 ACP 客户端
- [WeChat ACP](https://github.com/formulahendry/wechat-acp) — 微信消息桥接到 ACP Agent

---

## 价值提炼 & 与 Hermes 的关系

| 维度 | 说明 |
|------|------|
| **ACP 兼容性** | Hermes Agent 是 11 个预配置 Agent 之一，命令 `hermes acp` |
| **文件系统集成** | 通过 MCP 协议，Agent 可读写 VS Code 工作区文件 |
| **终端执行** | Agent 可实时执行命令并查看输出 |
| **权限模型** | 默认 `ask` 模式，可改为 `allowAll`，对应 Hermes 的审批策略 |
| **协议日志** | 可完整追踪 JSON-RPC 消息，便于调试 ACP 协议交互 |
| **会话管理** | 支持 Agent 自己的 `session/list` 或本地缓存 |
| **开发方式** | TypeScript + VS Code Extension API，npm 构建打包 |

---

## 参考链接

- GitHub: https://github.com/formulahendry/vscode-acp
- VS Code Marketplace: https://marketplace.visualstudio.com/items?itemName=formulahendry.acp-client
- Agent Client Protocol: https://agentclientprotocol.com/
- ACP UI: https://github.com/formulahendry/acp-ui
- WeChat ACP: https://github.com/formulahendry/wechat-acp
