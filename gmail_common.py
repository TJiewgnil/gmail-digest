#!/usr/bin/env python3
"""Shared Gmail API helpers: OAuth refresh-token flow + HTTPS requests.

Why HTTPS instead of IMAP/SMTP: the cloud routine sandbox blocks raw outbound
TCP to ports 993/465 (sockets fail with "Address family not supported"), but
allows HTTPS(443). The Gmail REST API is entirely 443, so it runs in the cloud.

Credentials come from environment variables (set them as cloud routine secrets,
or in a local `.env`):
    GMAIL_CLIENT_ID       OAuth 2.0 client id
    GMAIL_CLIENT_SECRET   OAuth 2.0 client secret
    GMAIL_REFRESH_TOKEN   long-lived refresh token (from gmail_oauth_setup.py)
    GMAIL_USER            your gmail address (digest recipient / From header)

Standard library only; no pip install needed.
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

# Force UTF-8 on the output streams: on Windows the console/pipe defaults to the
# locale codepage (gbk) which cannot encode much of the Unicode found in email.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

TOKEN_URL = "https://oauth2.googleapis.com/token"
API_BASE = "https://gmail.googleapis.com/gmail/v1"
# Read the inbox + send the digest. Send delivers the digest to a dedicated
# Gmail label (via a +digest alias) so the phone's Gmail app can notify on it.
SCOPES = (
    "https://www.googleapis.com/auth/gmail.readonly "
    "https://www.googleapis.com/auth/gmail.send"
)
HTTP_TIMEOUT = 30


def load_dotenv():
    """Load KEY=VALUE lines from a `.env` next to this file.

    Real environment variables always win (so cloud routine secrets override the
    file). A missing `.env` is fine — we just rely on the environment then.
    """
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))
    except OSError:
        pass


def _require(name):
    val = os.environ.get(name)
    if not val:
        sys.stderr.write(
            "ERROR: environment variable {} is not set. This project needs "
            "GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET and GMAIL_REFRESH_TOKEN "
            "(run gmail_oauth_setup.py once to obtain the refresh token).\n".format(name)
        )
        sys.exit(2)
    return val.strip()


def get_access_token():
    """Exchange the long-lived refresh token for a short-lived access token."""
    data = urllib.parse.urlencode({
        "client_id": _require("GMAIL_CLIENT_ID"),
        "client_secret": _require("GMAIL_CLIENT_SECRET"),
        "refresh_token": _require("GMAIL_REFRESH_TOKEN"),
        "grant_type": "refresh_token",
    }).encode("utf-8")
    req = urllib.request.Request(TOKEN_URL, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            return json.load(resp)["access_token"]
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        sys.stderr.write("ERROR: OAuth token refresh failed (HTTP {}): {}\n".format(e.code, body))
        sys.exit(1)
    except urllib.error.URLError as e:
        sys.stderr.write("ERROR: cannot reach {} : {}\n".format(TOKEN_URL, e.reason))
        sys.exit(1)


def _request(method, path, token, params=None, payload=None):
    url = API_BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    data = None
    headers = {"Authorization": "Bearer " + token}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        sys.stderr.write("ERROR: Gmail API {} {} failed (HTTP {}): {}\n".format(method, path, e.code, body))
        sys.exit(1)
    except urllib.error.URLError as e:
        sys.stderr.write("ERROR: cannot reach Gmail API ({}): {}\n".format(url, e.reason))
        sys.exit(1)


def api_get(path, token, params=None):
    return _request("GET", path, token, params=params)


def api_post(path, token, payload):
    return _request("POST", path, token, payload=payload)
