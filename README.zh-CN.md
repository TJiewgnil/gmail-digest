# gmail-digest 每日邮件摘要

[English](README.md) · **中文**

一个可复用、可自助安装的**每日邮件摘要**工具。把任意邮箱
（Outlook/Office 365、QQ/Foxmail、163/126、Yahoo、iCloud、学校邮箱……）转发进**同一个
Gmail**，由 **Claude Code 云端 routine** 每天给你发一份经过筛选、总结好的摘要。

- 通过 **Gmail API（HTTPS）** 读取邮件 —— 能在屏蔽 IMAP/SMTP 的 routine 云端沙箱里运行。
- **无需 API key** —— 总结由 Claude 本身完成。
- **纯 Python 标准库** —— 永远不需要 `pip install`。

## 工作原理

```
   QQ / Outlook / 学校邮箱 … ──转发──> Gmail 收件箱
                                          │  每天由 Claude Code 云端 routine 触发
                                          ▼
   fetch_inbox.py ──Gmail API──> 过去 24 小时邮件（JSON）
                                          ▼
   Claude 按 ROUTINE.md 筛选 + 总结 ──> digest.md
                                          ▼
   send_digest.py ──Gmail API──> 你的+digest@gmail.com ──> 手机通知
```

摘要同时也是 routine 自身的输出，可以在 claude.ai 的 routine 运行记录里回看。

## 快速开始

1. **Google Cloud（唯一不可省的人工步骤）。** 启用 Gmail API、配置 OAuth 同意屏幕
   （把自己加成 **Test user**）、创建一个 **Desktop app** OAuth 客户端。逐步点击说明
   （含两个坑）见 **[docs/SETUP.zh-CN.md](docs/SETUP.zh-CN.md)**。
2. **在自己电脑上运行向导：**
   ```bash
   python setup.py
   ```
   它会自动探测你的 `client_secret_*.json`，跑 OAuth 流程，写 `.env`，并自检（取信 + 发信）。
3. **创建云端 routine** —— 见 [docs/SETUP.zh-CN.md](docs/SETUP.zh-CN.md) 第 3 节。
4. **把其他邮箱转发进 Gmail** —— [docs/FORWARDING.zh-CN.md](docs/FORWARDING.zh-CN.md)。
5. **给摘要配一个手机通知** —— [docs/NOTIFICATIONS.zh-CN.md](docs/NOTIFICATIONS.zh-CN.md)。
6. **自定义 `ROUTINE.md`** —— 你的筛选/总结规则与输出格式。

## 文件说明

| 文件 | 作用 |
|---|---|
| `ROUTINE.md` | routine 的提示词：筛选/总结规则与输出格式（按需修改） |
| `fetch_inbox.py` | 通过 Gmail API 读取近期邮件 → JSON（`--hours/--label/--max/--query`） |
| `send_digest.py` | 通过 Gmail API 发送摘要（`--to` / `DIGEST_TO` / `+digest` 别名） |
| `gmail_common.py` | OAuth 刷新 + HTTPS 辅助函数（标准库） |
| `gmail_oauth_setup.py` | 一次性本地 OAuth 助手 → refresh token |
| `setup.py` | 一键安装向导 |
| `.claude/settings.json` | 允许 routine 无需确认地运行脚本 |
| `.env.example` | 配置模板（仅占位符） |

## 配置

所有配置都是环境变量 —— 在 routine 的云端环境里设为密钥，本地运行时放 `.env`。
见 [`.env.example`](.env.example)：

- `GMAIL_CLIENT_ID`、`GMAIL_CLIENT_SECRET`、`GMAIL_REFRESH_TOKEN`、`GMAIL_USER` —— Gmail 访问。
- `DIGEST_TO`（可选）—— 收件人覆盖；默认发到你的 `+digest` 别名。

回溯时间窗由 `ROUTINE.md` 里的 `--hours` 决定。

## 安全

- `.env`、`client_secret_*.json`、`token.json`、`inbox.json`、`digest.md` 都已被 git 忽略。
  绝不要提交任何密钥。
- 随时可在 <https://myaccount.google.com/permissions> 撤销本应用对 Gmail 的访问权限。

## 许可证

[MIT](LICENSE)。
