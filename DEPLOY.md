# 🏋️ Workout Bot — 部署指南

## 步骤 1：准备 GitHub 仓库

1. 去 https://github.com 创建新仓库，命名 `workout-bot`
2. 把以下文件上传：
   - main.py
   - gemini_helper.py
   - excel_helper.py
   - requirements.txt
   - Procfile
   - .gitignore
   （⚠️ 不要上传 .env 文件！）

## 步骤 2：部署到 Railway

1. 去 https://railway.app 注册（用 GitHub 登录）
2. 点 **New Project** → **Deploy from GitHub repo**
3. 选你的 `workout-bot` 仓库
4. 点 **Variables**，添加以下环境变量：

   | Key | Value |
   |-----|-------|
   | BOT_TOKEN | 你的 Telegram Bot Token |
   | GEMINI_API_KEY | 你的 Gemini API Key |

5. Railway 会自动部署，等 1-2 分钟

## 步骤 3：测试

打开 Telegram，找你的 bot，发 `/start`

然后发一条运动记录，例如：
> 今天练腿，深蹲4组10下100kg，腿举3组15下150kg，跑步20分钟

## 关于 Excel 文件

因为 Railway 是云端，Excel 文件会保存在 Railway 服务器上。
要下载 Excel，可以：
- 在 bot 加一个 `/download` 命令（之后可以加）
- 或者每周手动从 Railway 下载

## ⚠️ 安全提醒

去 @BotFather → /mybots → 你的 bot → API Token → Revoke
重新生成一个新 token，然后更新 Railway 的环境变量。
