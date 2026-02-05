---
name: tg-checkin
description: Generic Telegram Web automation for group check-ins. Supports multiple groups via configuration.
metadata:
  {
    "openclaw": {
      "requires": { "plugins": ["browser"] }
    }
  }
---

# tg-checkin Skill

自动化 Telegram 网页端群组签到工具。

## 功能
- 自动打开 Telegram 网页版 (https://web.telegram.org/a/)。
- 依次定位用户定义的群组并发送“签到”指令。
- 汇总签到结果。

## 配置
在使用此技能前，请在技能目录下创建或修改 `config.json`，列出你想要自动签到的群组名称：

```json
{
  "groups": [
    "群组名称1",
    "群组名称2"
  ]
}
```

## 使用方法
直接对 AI 说：
- "帮我签到那几个群"
- "运行 tg-checkin"

## 注意事项
1. **首次运行**：AI 会把网页版登录二维码发给你，请在手机上扫码登录一次，之后会自动记住。
2. **群名匹配**：请确保 `config.json` 里的群名与 Telegram 侧边栏显示的完全一致。
