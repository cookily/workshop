# hermes-web-ui 管理面板

社区维护的 Hermes Agent Web 管理面板。
GitHub: https://github.com/EKKOLearnAI/hermes-web-ui（6k+ star）
默认端口：8648

## 功能矩阵

| 功能 | 说明 | 版本 |
|------|------|------|
| 多会话管理 | 创建/重命名/删除/切换会话 | v0.4.0 |
| 每会话 Token 用量 | 输入/输出 Token、缓存命中率 | v0.4.0 |
| 用量分析面板 | 30 天趋势图、模型分布、估算成本 | v0.4.0 |
| 8 平台配置 | 飞书/Telegram/Discord/Slack/WhatsApp/微信/企微/Matrix | v0.4.0 |
| 定时任务管理 | 创建/编辑/暂停/恢复/删除 cron 任务 | v0.4.0 |
| 多 Profile 网关管理 | 启动/停止/监控各 profile 网关 | v0.4.0 |
| 文件浏览器 | 浏览/上传/下载/重命名/删除（本地/Docker/SSH） | v0.4.0 |
| 群聊 | 多 Agent 聊天室、@提及路由 | v0.4.0 |
| 技能与记忆 | 浏览/搜索/查看技能 | v0.4.0 |
| Web 终端 | 嵌入 Hermes TUI（node-pty） | v0.4.0 |
| 认证 | Token 认证、管理员账户、登录锁定 | v0.4.0 |

## 安装

### npm 安装（推荐）

```bash
npm install -g hermes-web-ui
hermes-web-ui start  # 默认 http://localhost:8648
```

### 一键安装脚本（Debian/Ubuntu/macOS）

自动检测系统并安装 Node.js（如缺失）+ hermes-web-ui。

### Docker Compose

```bash
# 单容器部署，内置 Hermes Agent 运行时
# 默认 http://localhost:6060
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `PORT` | `8648` | 监听端口 |
| `BIND_HOST` | `0.0.0.0` | 绑定地址（IPv6 需显式设 `::`） |
| `HERMES_WEB_UI_HOME` | `~/.hermes-web-ui` | 数据目录（Token、凭据、日志、DB） |
| `UPLOAD_DIR` | `$HERMES_WEB_UI_HOME/upload` | 上传根目录 |
| `CORS_ORIGINS` | `*` | CORS 源 |
| `AUTH_TOKEN` | 自动生成 | 认证 Bearer Token |
| `PROFILE` | `default` | 默认 Profile |
| `LOG_LEVEL` | `info` | 日志级别 |
| `MAX_DOWNLOAD_SIZE` | `200MB` | 最大下载文件大小 |
| `MAX_EDIT_SIZE` | `10MB` | 最大可编辑文件大小 |
| `WORKSPACE_BASE` | `/opt/data/workspace` | 工作区浏览根目录 |

## CLI 命令

| 命令 | 说明 |
|------|------|
| `hermes-web-ui start` | 后台启动 |
| `hermes-web-ui start --port 9000` | 指定端口启动 |
| `hermes-web-ui stop` | 停止 |
| `hermes-web-ui restart` | 重启 |
| `hermes-web-ui status` | 查看状态 |
| `hermes-web-ui update` | 更新到最新版并重启 |
| `hermes-web-ui -v` | 版本号 |

## 架构

```
Browser → BFF (Koa, :8648) → Socket.IO /chat-run
                ↓
        Hermes agent bridge → Hermes Agent runtime
                ↓
           Hermes CLI / profiles
```

BFF 层处理：Socket.IO 聊天流、Hermes agent bridge、Profile 感知的文件上传/下载（多后端）、会话 CRUD、账户/Profile 管理、配置/凭据管理、模型发现、技能/记忆管理、日志读取、静态文件服务。

## ⚠️ 常见陷阱

### 网关冲突（必读）

**问题**：hermes-web-ui 启动时自动扫描并尝试启动所有 profile 的网关。如果已有 systemd 网关（`hermes-gateway.service`）正在运行，两个网关共用同一个飞书 app_id，导致 Web UI 内部网关的飞书连接失败。

**症状**：
```
ERROR gateway.platforms.feishu: [Feishu] Another local Hermes gateway
is already using this Feishu app_id (PID xxx). Stop the other gateway
before starting a second Feishu websocket client.
```

**解法**：Web UI 需要独占网关，不能与 systemd 服务共享飞书连接。

```bash
# 启动 Web UI 前
systemctl --user stop hermes-gateway.service
hermes-web-ui start

# 恢复原状
hermes-web-ui stop
systemctl --user start hermes-gateway.service
```

**注意**：`systemctl --user stop` 触发 graceful drain（60s），可能超时。如果 `systemctl --user is-active` 仍显示 "deactivating"，等 drain 完成即可。Web UI 会检测到已存在的网关进程并自动调整端口分配。

**Web UI 的网关扫描逻辑**: 启动时 BFF 调用 `ensureProfileGatewaysRunning()`，扫描所有 profile 和已有网关进程。若端口冲突（如旧 zongguan2 profile 网关已占 8642 端口），自动重新分配（如 default → 8643）。Web UI BFF 设置 upstream 为第一个活跃的网关（通常是最早启动的 zongguan2 profile 网关或新起的 default profile 网关）。

### 会话可见性限制（v0.4.0）

Web UI 的会话侧边栏只显示自己产生的会话（API SERVER 来源）和 CLI 会话。飞书/Telegram 等外部平台的历史会话**不显示在侧边栏**。

**数据位置**：历史会话在 `~/.hermes/state.db`（187+ 条记录），Web UI 可通过 `/api/hermes/sessions` API 读取，但 UI 侧边栏不展示。

**查看方式**：
1. 在 Chat 页面新建会话后 Resume 历史会话
2. 直接调用 API：
   ```bash
   curl http://localhost:8648/api/hermes/sessions?limit=50 \
     -H "Authorization: Bearer $(cat ~/.hermes-web-ui/.token)"
   ```
3. 升级到 v0.6.1（右上角 Upgrade 按钮）

### Web UI 的会话 DB 与 state.db 的关系

| 数据库 | 位置 | 包含的会话 | 用途 |
|--------|------|-----------|------|
| Web UI 自身 DB | `~/.hermes-web-ui/hermes-web-ui.db` | Web UI Chat + CLI 会话 | 侧边栏展示、Ctrl+K 搜索 |
| Hermes state.db | `~/.hermes/state.db` | 所有平台（飞书/Telegram/CLI/cron）会话（187+ 条） | 只读历史、API 查询 |
| Profile gateway DB | `~/.hermes/profiles/<name>/state.db` | 仅该 profile 产生的会话 | Profile 隔离 |

**重要**：Ctrl+K 搜索**只搜索** Web UI 自身数据库，不搜索 Hermes state.db。

## 启动后检查清单

- [ ] `ss -tlnp \| grep 8648` — Web UI BFF 在监听
- [ ] `curl -s -o /dev/null -w "%{http_code}" http://localhost:8648/` — 返回 200
- [ ] 浏览器访问 `http://<服务器IP>:8648` — 看到登录页
- [ ] 输入 Token（`cat ~/.hermes-web-ui/.token`）登录
- [ ] 侧边栏能看到 CLI/API SERVER 会话
- [ ] API 测试：`curl http://localhost:8648/api/hermes/sessions?limit=3 -H "Authorization: Bearer $(cat ~/.hermes-web-ui/.token)"`