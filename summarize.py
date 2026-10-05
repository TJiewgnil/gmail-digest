#!/usr/bin/env python3
"""Summarize an inbox JSON dump into a digest via the Anthropic Messages API.

This is the "summarizer" for the GitHub Actions and local-cron deployments. The
Claude Code routine deployment does not need it (Claude Code is the summarizer).

It reads two inputs:
  1. the rules/prompt template (ROUTINE.md by default), and
  2. the inbox JSON produced by fetch_inbox.py (a path argument, or stdin),
calls the Anthropic Messages API over HTTPS with the standard library only, and
writes the finished digest to stdout (and optionally a file via --out).

Why urllib and not the `anthropic` SDK: the whole project is deliberately
zero-dependency (standard library only), so one script set runs identically in
CI, locally, and inside sandboxes with no `pip install`. This mirrors the HTTPS
pattern already used in gmail_common.py for the Gmail API.

Environment:
    ANTHROPIC_API_KEY   required — your Anthropic API key (sk-ant-...).
    ANTHROPIC_MODEL     optional — model id (default "claude-haiku-4-5").

Usage:
    python summarize.py inbox.json
    python fetch_inbox.py --hours 24 | python summarize.py
    python summarize.py inbox.json --out digest.md
    python summarize.py inbox.json --rules ROUTINE.md

Standard library only; no pip install needed.
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request

# Importing gmail_common reuses its load_dotenv() and, as a side effect, forces
# UTF-8 on stdout/stderr (so Windows consoles don't mangle Chinese / emoji).
from gmail_common import load_dotenv

API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_MODEL = "claude-haiku-4-5"
MAX_TOKENS = 4000
HTTP_TIMEOUT = 120

SYSTEM_PROMPT = (
    "You are an email digest assistant. Follow the user's rules exactly. "
    "The inbox contents are already provided to you below as JSON — do NOT try "
    "to run any scripts, tools, or commands; just read the JSON. "
    "Output ONLY the final digest text itself: no preamble, no explanation, and "
    "no surrounding code fences."
)


def _fail(msg, code=1):
    sys.stderr.write("ERROR: " + msg + "\n")
    sys.exit(code)


def read_rules(path):
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            return f.read()
    except OSError as e:
        _fail("cannot read rules file {}: {}".format(path, e), 2)


def read_inbox(path):
    """Read the inbox JSON from a file path, or from stdin when path is None."""
    if path is None or path == "-":
        data = sys.stdin.read()
        if not data.strip():
            _fail("no inbox JSON on stdin (pass a file path, or pipe fetch_inbox.py)", 2)
    else:
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                data = f.read()
        except OSError as e:
            _fail("cannot read inbox file {}: {}".format(path, e), 2)
    # Validate that it parses, and normalize the text we forward to the model.
    try:
        parsed = json.loads(data)
    except json.JSONDecodeError as e:
        _fail("inbox input is not valid JSON: {}".format(e), 2)
    return json.dumps(parsed, ensure_ascii=False, indent=2), parsed


def call_anthropic(api_key, model, system, user_content):
    payload = {
        "model": model,
        "max_tokens": MAX_TOKENS,
        "system": system,
        "messages": [{"role": "user", "content": user_content}],
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=data,
        method="POST",
        headers={
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            body = json.load(resp)
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        hint = ""
        if e.code == 401:
            hint = " — check ANTHROPIC_API_KEY (unauthorized)."
        elif e.code == 429:
            hint = " — rate limited or out of credit; retry later."
        elif 500 <= e.code < 600:
            hint = " — Anthropic server error; retry later."
        # Try to surface the API's own error message instead of a traceback.
        detail = raw
        try:
            err = json.loads(raw).get("error", {})
            if err.get("message"):
                detail = err["message"]
        except (ValueError, AttributeError):
            pass
        _fail("Anthropic API request failed (HTTP {}){}\n{}".format(e.code, hint, detail))
    except urllib.error.URLError as e:
        _fail("cannot reach the Anthropic API ({}): {}".format(API_URL, e.reason))

    # Expected shape: {"content": [{"type": "text", "text": "..."}], ...}
    try:
        parts = body.get("content", [])
        text = "".join(p.get("text", "") for p in parts if p.get("type") == "text")
    except AttributeError:
        text = ""
    if not text.strip():
        _fail("Anthropic API returned no text content:\n{}".format(
            json.dumps(body, ensure_ascii=False)[:1000]))
    return text.strip()


def main():
    load_dotenv()
    ap = argparse.ArgumentParser(
        description="Summarize an inbox JSON dump into a digest via the Anthropic Messages API.")
    ap.add_argument("inbox", nargs="?", default=None,
                    help="path to inbox JSON (default: read from stdin)")
    ap.add_argument("--rules", default=None,
                    help="path to the rules/prompt template (default: ROUTINE.md next to this script)")
    ap.add_argument("--out", default=None,
                    help="also write the digest to this file (always printed to stdout too)")
    ap.add_argument("--model", default=None,
                    help="override the model (else ANTHROPIC_MODEL, else {})".format(DEFAULT_MODEL))
    args = ap.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        _fail("ANTHROPIC_API_KEY is not set (export it, or add it to .env)", 2)
    model = args.model or os.environ.get("ANTHROPIC_MODEL") or DEFAULT_MODEL

    rules_path = args.rules or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "ROUTINE.md")
    rules = read_rules(rules_path)
    inbox_json, parsed = read_inbox(args.inbox)

    count = len(parsed) if isinstance(parsed, list) else "?"
    user_content = (
        rules
        + "\n\n---\n\nHere is the inbox as JSON ({} message(s)). "
          "Summarize it per the rules above.\n\n".format(count)
        + inbox_json
    )

    digest = call_anthropic(api_key, model, SYSTEM_PROMPT, user_content)

    if args.out:
        try:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(digest + "\n")
        except OSError as e:
            _fail("cannot write {}: {}".format(args.out, e))

    print(digest)


if __name__ == "__main__":
    main()
