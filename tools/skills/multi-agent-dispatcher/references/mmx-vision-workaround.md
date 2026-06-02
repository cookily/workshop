# MiniMax Vision API 接入指南

## 内置 vision_analyze 失败时的替代方案

### 问题现象
```python
vision_analyze(image_url=...) 
# → Error: 401 authentication_error, invalid api key
```

`vision_analyze` 是内置视觉服务，走独立认证体系，可能因配置问题返回 401。

### 解决方案：mmx vision describe

安装 MiniMax CLI 后，直接调 mmx 接口：

```bash
mmx vision describe /path/to/image.jpg
```

**实测有效**（2026-05-18）：
- 文件：PNG 1024×1536，约 2.9MB
- 返回：JSON 含完整图片描述（动漫风格多智能体架构图）
- 无 401 问题

### mmx 安装步骤（已验证）
```bash
# 1. 全局安装
npm install -g mmx-cli
mmx --version  # → 1.0.15

# 2. 配置 API key
mmx auth login --api-key <your-api-key>

# 3. 视觉分析
mmx vision describe /path/to/image.jpg
```

### mmx 可用资源（Token Plan 额度）
```
MiniMax-M*     584/1500   # 主模型
coding-plan-vlm   0/150    # 视觉理解
coding-plan-search 0/150   # 搜索
```

## Compression Threshold 配置

内置在 `~/.hermes/config.yaml`：
```yaml
compression:
  enabled: true
  threshold: 0.8   # 原值 0.5，改成 0.8 减少压缩频率
```
