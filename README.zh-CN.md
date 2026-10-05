# gmail-digest 每日邮件摘要

[English](README.md) · **中文**

一个可复用、可自助安装的**每日邮件摘要**工具。把任意邮箱
（Outlook/Office 365、QQ/Foxmail、163/126、Yahoo、iCloud、学校邮箱……）转发进**同一个
Gmail**，就能定时收到一份经过筛选、由大模型总结的摘要。

- 通过 **Gmail API（HTTPS）** 读取邮件 —— 任何环境都能跑，包括屏蔽 IMAP/SMTP 的沙箱和 CI。
- **纯 Python 标准库** —— 永远不需要 `pip install`。
- 三种运行方式，每种都是同一条三段式流水线。

## 工作原理

```
        ┌─────────────┐     ┌──────────────┐     ┌──────────────┐
        │ fetch_inbox │ --> │  summarize   │ --> │ send_digest  │
        │ （Gmail API）│     │ （规则总结）  │     │ （Gmail API）│
        └─────────────┘     └──────────────┘     └──────────────┘
           inbox.json          digest.md            你的收件箱
```

流水线永远是 **取信 → 总结 → 投递**。不同部署方式只是**触发方式**和**由谁来总结**不同：

| 部署方式 | 触发 | 总结者 | 需要 |
|---|---|---|---|
| **GitHub Actions + Anthropic API**（主推） | 工作流里的 cron | `summarize.py` | `ANTHROPIC_API_KEY` + GitHub secrets |
| **Claude Code routine** | `/schedule` | Claude Code（无需 API key） | Claude Code / claude.ai |
| **本地 cron / 任务计划** | 操作系统调度器 | `summarize.py` | 开着机 + API key |

## 快速开始

1. **Google Cloud（唯一不可省的人工步骤）。** 启用 Gmail API、配置 OAuth 同意屏幕
   （把自己加成 **Test user**）、创建一个 **Desktop app** OAuth 客户端。逐步点击说明
   （含两个坑）见 **[docs/SETUP.zh-CN.md](docs/SETUP.zh-CN.md)**。
2. **运行向导：**
   ```bash
   python setup.py
   ```
   它会自动探测你的 `client_secret_*.json`，跑 OAuth 流程，写 `.env`，自检（取信 + 发信），
   还能帮你把 GitHub Actions 的密钥推上去。
3. **选择一种部署方式**（GitHub Actions / Claude Code routine / 本地）——见
   [docs/SETUP.zh-CN.md](docs/SETUP.zh-CN.md) 第 3 节。
4. **把其他邮箱转发进 Gmail** —— [docs/FORWARDING.zh-CN.md](docs/FORWARDING.zh-CN.md)。
5. **给摘要配一个手机通知** —— [docs/NOTIFICATIONS.zh-CN.md](docs/NOTIFICATIONS.zh-CN.md)。
6. **自定义 `ROUTINE.md`** —— 你的筛选/总结规则与输出格式。

## 文件说明

| 文件 | 作用 |
|---|---|
| `fetch_inbox.py` | 通过 Gmail API 读取近期邮件 → JSON（`--hours/--label/--max/--query`） |
| `summarize.py` | inbox JSON + `ROUTINE.md` → 经 Anthropic Messages API 生成摘要 |
| `send_digest.py` | 通过 Gmail API 发送摘要（`--to` / `DIGEST_TO` / `+digest` 别名） |
| `gmail_common.py` | OAuth 刷新 + HTTPS 辅助函数（标准库） |
| `gmail_oauth_setup.py` | 一次性本地 OAuth 助手 → refresh token |
| `setup.py` | 一键安装向导 |
| `ROUTINE.md` | 可自定义的筛选/总结规则（也是 Claude Code routine 的 prompt） |
| `run_local.sh` / `run_local.ps1` | 本地端到端运行脚本（macOS/Linux / Windows） |
| `.github/workflows/daily-digest.yml` | 定时 CI 流水线 |
| `.env.example` | 配置模板（仅占位符） |

## 配置

所有配置都是环境变量（本地放 `.env`，或在 GitHub Actions 里设为 secrets/variables）。
见 [`.env.example`](.env.example)：

- `GMAIL_CLIENT_ID`、`GMAIL_CLIENT_SECRET`、`GMAIL_REFRESH_TOKEN`、`GMAIL_USER` —— Gmail 访问。
- `ANTHROPIC_API_KEY`、`ANTHROPIC_MODEL`（默认 `claude-haiku-4-5`）—— 总结器。
- `DIGEST_TO`（可选）、`DIGEST_HOURS`（默认 `24`）—— 投递。

## 成本

用 `claude-haiku-4-5` 总结一天的邮件，最多也就几美分。想要更高质量，设
`ANTHROPIC_MODEL=claude-sonnet-4-5`。

## 安全

- `.env`、`client_secret_*.json`、`token.json`、`inbox.json`、`digest.md` 都已被 git 忽略。
  绝不要提交任何密钥。
- 随时可在 <https://myaccount.google.com/permissions> 撤销本应用对 Gmail 的访问权限。

## 许可证

[MIT](LICENSE)。
