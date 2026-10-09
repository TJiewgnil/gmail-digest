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
- 一个能使用云端 routine 的 **Claude Code** 账号（<https://claude.ai/code>），以及一个用来
  存放本仓库的 **GitHub** 账号。

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
3. 询问 `GMAIL_USER` 和可选的收件人覆盖；
4. 写入 `.env`（已被 git 忽略）；
5. **自检**：取过去 24 小时的邮件（读），并发一封测试摘要（发）；
6. 打印创建云端 routine 的后续步骤。

想手动做？运行 `python gmail_oauth_setup.py --client-id <id> --client-secret
<secret>`，然后把 `.env.example` 复制成 `.env` 并填好。

---

## 3. 创建 Claude Code 云端 routine

由 Claude 充当总结器，所以不需要 API key，也没有单独的总结脚本 —— routine 照着
`ROUTINE.md` 做即可。

1. **把本仓库推到 GitHub**（私有仓库即可），并在 Claude Code 网页版
   （<https://claude.ai/code>）里连接它。
2. **为 routine 创建一个云端环境**，把以下变量设为环境密钥（值就在向导写好的 `.env` 里）：
   `GMAIL_CLIENT_ID`、`GMAIL_CLIENT_SECRET`、`GMAIL_REFRESH_TOKEN`、
   `GMAIL_USER`，以及可选的 `DIGEST_TO`。
3. **创建一个每日 routine**（在 Claude Code 里运行 `/schedule`，或用 claude.ai 的
   routines 页面），选本仓库 + 上面的环境，prompt 写类似：
   > 按 ROUTINE.md 里的说明执行。

   按 `ROUTINE.md`，每次运行会执行 `python fetch_inbox.py --hours 24`、总结邮件、写入
   `digest.md`、运行 `python send_digest.py digest.md`，并把摘要同时作为 routine 自身的输出，
   方便在运行记录里回看。`.claude/settings.json` 预先允许了运行 `python`，无人值守时不会卡在
   权限确认上。
   > ⏰ **routine 的 cron 是 UTC 时间，且不随夏令时调整。** 固定的 UTC 时间会在夏令时切换时
   > 让本地时间漂移 ±1 小时，例如 `0 10 * * *` 在中欧夏令时是 12:00、冬令时是 11:00。
   > 若要严格锁定本地时间，每年两次手动调整。
4. **测试：** 手动触发一次 routine，确认摘要邮件到达。

---

## 4. 手机通知

配置 Gmail 过滤器 + 标签，让摘要能推送到手机。具体做法以及关于安卓推送的经验教训，见
**[通知](NOTIFICATIONS.zh-CN.md)**。

---

## 5. 自定义 `ROUTINE.md`

`ROUTINE.md` 保存你的筛选优先级、来源映射、输出格式和语言。随意修改 —— 它是**唯一**控制
摘要样子的地方。

---

## 验证清单

- `python -m py_compile *.py` —— 所有脚本编译通过。
- `python fetch_inbox.py --hours 24` —— 打印收件箱 JSON。
- `python send_digest.py digest.md` —— 测试邮件到达你的 `+digest` 别名 / `DIGEST_TO`。
- 手动运行一次 routine，运行完成且摘要到达。

## 疑难排查

- **`403 access_denied`** → 把自己加成测试用户（第 1.3 步）。
- **没有返回 `refresh_token`** → Google 只在首次同意时返回。到
  <https://myaccount.google.com/permissions> 撤销本应用后重跑。
- **routine 运行报 `GMAIL_CLIENT_ID is not set`** → routine 的云端环境里没配密钥（第 3.2 步）。
- **Windows 上中文/表情乱码**（仅本地运行）→ 运行脚本前设置 `PYTHONUTF8=1`。
