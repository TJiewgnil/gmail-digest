# 安装配置

[English](SETUP.md) · **中文**

相关：[转发](FORWARDING.zh-CN.md) · [通知](NOTIFICATIONS.zh-CN.md)

**唯一**必须手动完成的是 Google Cloud 的 OAuth 配置（第 1 步）。之后的一切都由
`python setup.py` 自动完成。

---

## 0. 前置条件

- **Python 3.8+**（纯标准库 —— 无需 `pip install`）。
- 一个用来**汇总收取所有邮件的 Gmail 账号**（之后再配置转发，见
  [转发](FORWARDING.zh-CN.md)）。
- 走 GitHub Actions / 本地路线的话：一个 **Anthropic API key**
  （<https://console.anthropic.com/>）。
- 可选（用于自动推送 CI 密钥）：**GitHub CLI**（`gh`）。

---

## 1. Google Cloud OAuth（唯一的人工步骤）

在 <https://console.cloud.google.com/> 做一次即可。

1. **创建或选择一个项目**（顶部项目选择器 → *新建项目*）。
2. **启用 Gmail API：** *API 和服务 → 库* → 搜索 “Gmail API” → **启用**。
3. **配置 OAuth 同意屏幕：** *API 和服务 → OAuth 同意屏幕*。
   - 用户类型：**外部（External）** → *创建*。
   - 按要求填写应用名称和你的邮箱。
   - **把自己加成测试用户（Test user）。** *目标用户 / 测试用户 → 添加用户 →* 填你的
     Gmail 地址。
     > ⚠️ **坑 #1。** 不加这一步，授权会以 **`403 access_denied`**（“应用正在测试中”）
     > 失败。把自己加成测试用户即可解决。（个人使用**无需**发布应用或通过验证。）
4. **创建 OAuth 客户端：** *API 和服务 → 凭据 → 创建凭据 → OAuth 客户端 ID*。
   - 应用类型：**桌面应用（Desktop app）**（只有它才允许本工具用的
     `http://localhost` 回环重定向）。
   - 如果 Google 显示类似 **“此应用将由 AI 智能体使用”** 的复选框，**请留空不要勾选。**
     > ⚠️ **坑 #2。** 勾选它会改变客户端允许的流程，破坏这里用到的桌面回环授权。
   - 创建后 **下载 JSON**。把它存到仓库目录，命名为 `client_secret_*.json`
     （任何以 `client_secret` 开头的名字都行）。该文件已被 git 忽略。

---

## 2. 运行安装向导

```bash
python setup.py
```

它会：

1. 自动探测 `client_secret_*.json`，读出 client id/secret；
2. 打开浏览器完成 Google 授权 → 拿到 **refresh token**；
3. 询问 `GMAIL_USER`、`ANTHROPIC_API_KEY`、模型、收件人、回溯小时数；
4. 写入 `.env`（已被 git 忽略）；
5. **自检**：取过去 24 小时的邮件（读），并发一封测试摘要（发）；
6. 可选地运行 `gh secret set`，把 GitHub Actions 密钥推上去；
7. 打印你所选部署方式的后续步骤。

想手动做？运行 `python gmail_oauth_setup.py --client-id <id> --client-secret
<secret>`，然后把 `.env.example` 复制成 `.env` 并填好。

---

## 3. 三选一：部署方式

### 3a. GitHub Actions + Anthropic API（主推，推荐）

在云端按计划运行 —— 你的机器上不留任何东西。

1. 把本仓库推到 GitHub。
2. 设置以下 **Actions secrets**（*Settings → Secrets and variables → Actions*），
   或让 `setup.py` 用 `gh` 帮你推：
   `GMAIL_CLIENT_ID`、`GMAIL_CLIENT_SECRET`、`GMAIL_REFRESH_TOKEN`、
   `GMAIL_USER`、`ANTHROPIC_API_KEY`。
   可选 **variables**（同一页面的 “Variables” 标签）：`ANTHROPIC_MODEL`、
   `DIGEST_TO`、`DIGEST_HOURS`。
3. 修改 `.github/workflows/daily-digest.yml` 里的 cron。
   > ⏰ **cron 是 UTC 时间，且不随夏令时调整。** 固定的 UTC 时间会在夏令时切换时让你本地
   > 的时间漂移 ±1 小时。请选一个对应你期望本地时间的 UTC 时刻，例如
   > `0 7 * * *` = UTC 07:00 = 北京时间 15:00、中欧冬令时 08:00 / 夏令时 09:00。
   > 若要严格锁定本地时间，每年两次手动调整。
4. 测试：*Actions → Daily Email Digest → Run workflow*。

### 3b. Claude Code routine（无需 API key）

这里由 Claude Code 充当总结器，所以**不需要** `ANTHROPIC_API_KEY`，也不需要
`summarize.py`。

1. 用 Claude Code / claude.ai 打开本仓库。
2. 用 `/schedule` 创建一个每日 routine，其 prompt 遵循 `ROUTINE.md`：运行
   `python fetch_inbox.py --hours 24`，按规则总结，写入 `digest.md`，再运行
   `python send_digest.py digest.md`。
3. 摘要同时会作为 routine 自身的输出打印出来，方便你在运行记录里回看。

把 `GMAIL_CLIENT_ID`、`GMAIL_CLIENT_SECRET`、`GMAIL_REFRESH_TOKEN`、`GMAIL_USER`
设为该 routine 的环境密钥。

### 3c. 本地 cron / 任务计划

在你自己常开的机器上运行。需要在 `.env` 里有 `ANTHROPIC_API_KEY`。

- **macOS / Linux：**
  ```bash
  ./run_local.sh          # 单次测试
  ```
  然后加一条 crontab（`crontab -e`）：
  ```cron
  0 8 * * *  cd /path/to/gmail-digest && ./run_local.sh >> digest.log 2>&1
  ```
  本地 cron 使用本机本地时间（无需 UTC 换算）。

- **Windows：**
  ```powershell
  powershell -ExecutionPolicy Bypass -File .\run_local.ps1
  ```
  然后在**任务计划程序**里创建一个每日的基本任务：
  - 程序：`powershell.exe`
  - 参数：`-ExecutionPolicy Bypass -File "C:\path\to\gmail-digest\run_local.ps1"`

---

## 4. 手机通知

配置 Gmail 过滤器 + 标签，让摘要能推送到手机。具体做法以及关于安卓推送的经验教训，见
**[通知](NOTIFICATIONS.zh-CN.md)**。

---

## 5. 自定义 `ROUTINE.md`

`ROUTINE.md` 保存你的筛选优先级、来源映射、输出格式和语言。随意修改 —— 它是**唯一**控制
摘要样子的地方，三种部署方式都读它。

---

## 验证清单

- `python -m py_compile *.py` —— 所有脚本编译通过。
- `python fetch_inbox.py --hours 24` —— 打印收件箱 JSON。
- `python summarize.py inbox.json` —— 打印摘要（需 `ANTHROPIC_API_KEY`）。
- `python send_digest.py digest.md` —— 测试邮件到达你的 `+digest` 别名 / `DIGEST_TO`。
- GitHub Actions：`workflow_dispatch` 运行变绿，摘要到达。

## 疑难排查

- **`403 access_denied`** → 把自己加成测试用户（第 1.3 步）。
- **没有返回 `refresh_token`** → Google 只在首次同意时返回。到
  <https://myaccount.google.com/permissions> 撤销本应用后重跑。
- **Anthropic 返回 `401`** → 检查 `ANTHROPIC_API_KEY`。
- **Anthropic 返回 `429`** → 限流或额度用尽；稍后重试。
- **Windows 上中文/表情乱码** → 脚本已强制 UTF-8；请通过 `run_local.ps1` 运行
  （它会设置控制台编码）。
