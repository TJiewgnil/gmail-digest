# Local fallback runner for the daily email digest.
# Use this with Windows Task Scheduler if the cloud routine can't reach IMAP/SMTP.
# It loads .env, fetches the inbox, asks headless Claude to summarize, and emails the digest.
#
# Manual test:   powershell -ExecutionPolicy Bypass -File .\run_local.ps1

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

# Force UTF-8 across the whole pipeline. Windows PowerShell 5.1 otherwise decodes
# python's stdout with the locale codepage (gbk) and encodes text piped into claude
# as ASCII — either one turns Chinese subjects / bodies / emoji into mojibake.
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONUTF8 = "1"

# --- load .env into the process environment ---
if (Test-Path ".env") {
  Get-Content ".env" | ForEach-Object {
    if ($_ -match '^\s*([^#=]+)=(.*)$') {
      Set-Item -Path ("Env:" + $matches[1].Trim()) -Value $matches[2].Trim()
    }
  }
} else {
  throw ".env not found — copy .env.example to .env and fill in credentials."
}

# --- 1. fetch last 24h of mail ---
$inbox = & python fetch_inbox.py --hours 24
if ($LASTEXITCODE -ne 0) { throw "fetch_inbox.py failed (exit $LASTEXITCODE)" }
$inbox | Out-File -Encoding utf8 inbox.json
Write-Output "Fetched inbox.json"

# --- 2. summarize with headless Claude (inbox passed inline so no file tools are needed) ---
$rules  = Get-Content "ROUTINE.md" -Raw -Encoding UTF8
$prompt = $rules + "`n`n只输出最终的中文摘要正文本身，不要任何前言、解释或代码块标记。" `
        + "不要真的运行脚本，直接根据下面的 inbox.json 内容生成摘要：`n`n" + $inbox
$prompt | & claude -p --output-format text | Out-File -Encoding utf8 digest.md
if ($LASTEXITCODE -ne 0) { throw "claude summarization failed (exit $LASTEXITCODE)" }
Write-Output "Wrote digest.md"

# --- 3. email the digest back to yourself ---
& python send_digest.py digest.md
if ($LASTEXITCODE -ne 0) { throw "send_digest.py failed (exit $LASTEXITCODE)" }
Write-Output "Done: digest sent."
