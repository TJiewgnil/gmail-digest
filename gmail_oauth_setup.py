#!/usr/bin/env python3
"""One-time LOCAL helper to obtain a Gmail API refresh token via OAuth.

Run this ONCE on your own machine (it needs a browser). It:
  1. opens Google's consent screen,
  2. captures the redirect on http://localhost:<port>,
  3. exchanges the authorization code for tokens,
  4. prints GMAIL_REFRESH_TOKEN for you to store as a secret.

Prereqs (in Google Cloud Console first):
  - Create / pick a project, then enable the "Gmail API".
  - OAuth consent screen: User type = External; add your gmail as a Test user.
  - Credentials -> Create OAuth client ID -> Application type "Desktop app".
    (Desktop apps allow the http://localhost loopback redirect used here.)
  - Copy the Client ID and Client secret.

Usage:
    python gmail_oauth_setup.py --client-id XXX --client-secret YYY
  (or set GMAIL_CLIENT_ID / GMAIL_CLIENT_SECRET in the env / .env first)

Standard library only.
"""
import argparse
import http.server
import json
import os
import secrets
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request
import webbrowser

from gmail_common import SCOPES, TOKEN_URL, load_dotenv

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"


class OAuthError(Exception):
    """Raised when the OAuth loopback flow cannot produce a refresh token."""


def _free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def run_oauth_flow(client_id, client_secret):
    """Run the loopback OAuth consent flow and return a refresh token.

    Opens the browser, serves one localhost redirect, exchanges the code for
    tokens and returns the refresh token. Raises OAuthError on any failure so
    callers (e.g. setup.py) can handle it without a traceback.
    """
    port = _free_port()
    redirect_uri = "http://localhost:{}/".format(port)
    state = secrets.token_urlsafe(16)
    auth_url = AUTH_URL + "?" + urllib.parse.urlencode({
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": SCOPES,
        "access_type": "offline",   # ask for a refresh token
        "prompt": "consent",        # force it even on re-consent
        "state": state,
    })

    captured = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            captured["code"] = (params.get("code") or [None])[0]
            captured["state"] = (params.get("state") or [None])[0]
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                "Authorization complete / 授权完成. You can close this tab.".encode("utf-8"))

        def log_message(self, *args):  # silence default logging
            pass

    print("Opening the browser for Google consent...")
    print("If it does not open, paste this URL manually:\n" + auth_url + "\n")
    webbrowser.open(auth_url)

    httpd = http.server.HTTPServer(("127.0.0.1", port), Handler)
    httpd.handle_request()  # serve exactly one redirect, then stop

    if not captured.get("code") or captured.get("state") != state:
        raise OAuthError("did not receive a valid authorization code.")

    data = urllib.parse.urlencode({
        "code": captured["code"],
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }).encode("utf-8")
    req = urllib.request.Request(TOKEN_URL, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            tok = json.load(resp)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise OAuthError("token exchange failed (HTTP {}): {}".format(e.code, body))
    except urllib.error.URLError as e:
        raise OAuthError("cannot reach {}: {}".format(TOKEN_URL, e.reason))

    refresh = tok.get("refresh_token")
    if not refresh:
        raise OAuthError(
            "no refresh_token returned. Google only returns one on the first "
            "consent — revoke this app at https://myaccount.google.com/permissions "
            "and run again.")
    return refresh


def main():
    load_dotenv()
    ap = argparse.ArgumentParser(description="Obtain a Gmail API refresh token (one-time).")
    ap.add_argument("--client-id", default=os.environ.get("GMAIL_CLIENT_ID"))
    ap.add_argument("--client-secret", default=os.environ.get("GMAIL_CLIENT_SECRET"))
    args = ap.parse_args()
    if not args.client_id or not args.client_secret:
        sys.stderr.write(
            "ERROR: provide --client-id/--client-secret (or set "
            "GMAIL_CLIENT_ID / GMAIL_CLIENT_SECRET in the environment or .env)\n"
        )
        sys.exit(2)

    try:
        refresh = run_oauth_flow(args.client_id, args.client_secret)
    except OAuthError as e:
        sys.stderr.write("ERROR: " + str(e) + "\n")
        sys.exit(1)

    print("\n=== SUCCESS ===")
    print("GMAIL_REFRESH_TOKEN=" + refresh)
    print(
        "\nStore GMAIL_USER, GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET and the token above\n"
        "as secrets on the cloud environment, and/or add them to your local .env."
    )


if __name__ == "__main__":
    main()
