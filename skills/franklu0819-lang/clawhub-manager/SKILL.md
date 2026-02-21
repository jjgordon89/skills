---
name: clawhub-manager
description: ClawHub 技能管理工具。封装技能的发布、删除、查询和搜索功能，方便管理 ClawHub 上的技能。
metadata: {
  "openclaw": {
    "requires": {
      "bins": ["clawhub"]
    }
  }
}

---

# ClawHub 管理技能

简化 ClawHub 技能的发布、删除、查询和搜索操作。

## 功能特性

- ✅ **发布技能** - 将本地技能发布到 ClawHub
- ✅ **删除技能** - 从 ClawHub 删除已发布的技能
- ✅ **查询技能** - 查看技能的详细信息和统计数据
- ✅ **搜索技能** - 在 ClawHub 上搜索技能
- ✅ **列出技能** - 列出本地已安装的技能

## 快速开始

### 查询技能信息

```bash
# 查询技能详情
bash /root/.openclaw/workspace/skills/clawhub-manager/scripts/inspect.sh feishu-voice

# 查询技能统计（JSON 格式）
bash /root/.openclaw/workspace/skills/clawhub-manager/scripts/inspect.sh feishu-voice --json
```

### 搜索技能

```bash
# 搜索技能（关键词）
bash /root/.openclaw/workspace/skills/clawhub-manager/scripts/search.sh "feishu"

# 搜索技能（限制结果数量）
bash /root/.openclaw/workspace/skills/clawhub-manager/scripts/search.sh "pdf" --limit 10
```

### 列出本地技能

```bash
# 列出所有已安装的技能
bash /root/.openclaw/workspace/skills/clawhub-manager/scripts/list.sh
```

### 发布技能

```bash
# 发布技能（指定版本）
bash /root/.openclaw/workspace/skills/clawhub-manager/scripts/publish.sh \
  /root/.openclaw/workspace/skills/your-skill \
  --version 1.0.0 \
  --changelog "首次发布"

# 发布技能（指定 slug 和名称）
bash /root/.openclaw/workspace/skills/clawhub-manager/scripts/publish.sh \
  /root/.openclaw/workspace/skills/your-skill \
  --slug your-slug \
  --name "Your Skill Name" \
  --version 1.0.0
```

### 删除技能

```bash
# 删除技能
bash /root/.openclaw/workspace/skills/clawhub-manager/scripts/delete.sh your-slug
```

## 使用场景

- 📦 **批量管理** - 一次性管理多个技能的发布和删除
- 📊 **数据统计** - 查看技能的下载量、安装量等统计数据
- 🔍 **技能发现** - 搜索和发现有用的技能
- 🔄 **版本管理** - 轻松发布新版本和更新技能

## 技能统计输出示例

```json
{
  "name": "Feishu Voice",
  "slug": "feishu-voice",
  "downloads": 19,
  "installs": 1,
  "stars": 0,
  "versions": 2,
  "updated": "2026-02-21 16:45"
}
```

## 🔒 安全注意事项

发布技能前，请确保：

1. ✅ **不在技能文件中硬编码任何密钥**
   - 所有 API Key、Secret、Token 必须使用环境变量
   - 使用占位符（如 `YOUR_API_KEY_HERE`）

2. ✅ **敏感信息存储在环境变量中**
   ```bash
   # ✅ 正确：从环境变量读取
   API_KEY="${API_KEY}"
   
   # ❌ 错误：硬编码密钥
   API_KEY="tvly-YOUR_REAL_KEY_HERE"
   ```

3. ✅ **.env 文件已添加到 .gitignore**
   - 防止敏感配置被提交到版本控制

4. ✅ **发布前会自动进行安全扫描**
   - 脚本会自动检测常见密钥泄露
   - 发现问题会阻止发布并提示修复

### 安全扫描功能

`publish.sh` 内置安全扫描，会自动检测：

- 🔑 **API 密钥**: Tavily (tvly-), OpenAI (sk-), GitHub (ghp_, gho_, ghu_, ghs_), Perplexity (pplx-), Exa (exa_)
- 🔐 **App Secret**: 检测 `app_secret=`, `app-secret=` 等模式
- 🎫 **Access Token**: 检测 `access_token=`, `access-token=` 等模式
- 📁 **敏感文件**: .env, .secrets, *.key, *.pem
- 🔧 **环境变量硬编码**: 检测 `export API_KEY=`, `export SECRET=` 等

### 手动安全检查

发布前也可以手动运行检查：

```bash
# 检查常见密钥格式
grep -r "tvly-\|sk-\|ghp_\|pplx-\|exa_" \
  --include="*.md" --include="*.sh" \
  --include="*.py" --include="*.js"

# 检查通用密钥模式
grep -ri "api[_-]?key\s*[=:]" \
  --include="*.sh" --include="*.py"
```

### 如果发现密钥泄露

1. ⚠️ **立即撤销**已泄露的密钥
2. 🔁 **重新生成**新的密钥
3. 📝 **替换为占位符**（如 `YOUR_API_KEY_HERE`）
4. 🧹 **从 Git 历史中清除**（如果已提交）

### 跳过安全扫描（不推荐）

```bash
# ⚠️ 仅在测试环境使用
bash publish.sh /path/to/skill --version 1.0.0 --skip-security
```

## 注意事项

1. **权限要求**
   - 发布和删除技能需要登录 ClawHub
   - 只能删除自己发布的技能

2. **版本号规范**
   - 遵循语义化版本（Semantic Versioning）
   - 格式：MAJOR.MINOR.PATCH（如 1.0.0）

3. **slug 命名**
   - 只能包含小写字母、数字和连字符
   - 一旦发布不能修改

4. **速率限制**
   - ClawHub 可能有 API 速率限制
   - 大量操作时建议添加延迟

## 作者

franklu0819-lang

## 许可证

MIT
