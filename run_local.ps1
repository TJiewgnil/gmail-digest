# Local runner for the daily email digest (Windows).
# Mirrors run_local.sh: load .env, fetch -> summarize.py -> send.
#
# Manual test:   powershell -ExecutionPolicy Bypass -File .\run_local.ps1
# Task Scheduler: create a Basic Task that runs, daily:
#   Program:   powershell.exe
#   Arguments: -ExecutionPolicy Bypass -File "C:\path\to\gmail-digest\run_local.ps1"

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

# Force UTF-8 across the whole pipeline. Windows PowerShell 5.1 otherwise decodes
# python's stdout with the locale codepage (gbk), turning Chinese subjects /
# bodies / emoji into mojibake.
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONUTF8 = "1"

$py    = if ($env:PYTHON) { $env:PYTHON } else { "python" }
$hours = if ($env:DIGEST_HOURS) { $env:DIGEST_HOURS } else { "24" }

# --- load .env into the process environment (real env vars still win) ---
if (Test-Path ".env") {
  Get-Content ".env" | ForEach-Object {
    if ($_ -match '^\s*([^#=]+)=(.*)$') {
      Set-Item -Path ("Env:" + $matches[1].Trim()) -Value $matches[2].Trim()
    }
  }
} else {
  throw ".env not found — copy .env.example to .env and fill in credentials, or run: python setup.py"
}

# --- 1. fetch last N hours of mail ---
$inbox = & $py fetch_inbox.py --hours $hours
if ($LASTEXITCODE -ne 0) { throw "fetch_inbox.py failed (exit $LASTEXITCODE)" }
$inbox | Out-File -Encoding utf8 inbox.json
Write-Output "Fetched inbox.json"

# --- 2. summarize via the Anthropic API (needs ANTHROPIC_API_KEY) ---
& $py summarize.py inbox.json --out digest.md | Out-Null
if ($LASTEXITCODE -ne 0) { throw "summarize.py failed (exit $LASTEXITCODE)" }
Write-Output "Wrote digest.md"

# --- 3. email the digest back to yourself ---
& $py send_digest.py digest.md
if ($LASTEXITCODE -ne 0) { throw "send_digest.py failed (exit $LASTEXITCODE)" }
Write-Output "Done: digest sent."
