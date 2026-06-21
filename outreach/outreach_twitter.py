import hashlib
import base64
import secrets
import urllib.parse
import webbrowser
import json
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread

import requests
from config import TWITTER_CLIENT_ID, TWITTER_CLIENT_SECRET, TWITTER_MESSAGE

TOKENS_FILE  = Path(__file__).parent / "sessions" / "twitter_tokens.json"
REDIRECT_URI = "http://localhost:8765/callback"
SCOPES       = "dm.write tweet.read users.read offline.access"

_auth_code = None


class _CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global _auth_code
        params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        _auth_code = params.get("code", [None])[0]
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"<h2>Authorized! You can close this tab.</h2>")

    def log_message(self, *_):
        pass


def _load_tokens() -> dict:
    if TOKENS_FILE.exists():
        with open(TOKENS_FILE) as f:
            return json.load(f)
    return {}


def _save_tokens(tokens: dict):
    TOKENS_FILE.parent.mkdir(exist_ok=True)
    with open(TOKENS_FILE, "w") as f:
        json.dump(tokens, f, indent=2)


def _refresh(refresh_token: str) -> dict:
    resp = requests.post(
        "https://api.twitter.com/2/oauth2/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": TWITTER_CLIENT_ID,
        },
        auth=(TWITTER_CLIENT_ID, TWITTER_CLIENT_SECRET),
    )
    resp.raise_for_status()
    return resp.json()


def authorize_twitter() -> str:
    """Return a valid access token, running the OAuth 2.0 PKCE flow if needed."""
    global _auth_code

    tokens = _load_tokens()
    if tokens.get("refresh_token"):
        try:
            new = _refresh(tokens["refresh_token"])
            _save_tokens({**tokens, **new})
            return new["access_token"]
        except Exception as e:
            print(f"  Token refresh failed ({e}), re-authorizing...")

    # PKCE
    code_verifier = secrets.token_urlsafe(50)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).rstrip(b"=").decode()

    auth_url = "https://twitter.com/i/oauth2/authorize?" + urllib.parse.urlencode({
        "response_type": "code",
        "client_id": TWITTER_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "state": secrets.token_urlsafe(16),
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    })

    server = HTTPServer(("localhost", 8765), _CallbackHandler)
    t = Thread(target=server.handle_request)
    t.start()

    print("  Opening browser for Twitter authorization...")
    webbrowser.open(auth_url)
    t.join(timeout=120)
    server.server_close()

    if not _auth_code:
        raise RuntimeError("Twitter authorization timed out or was cancelled.")

    resp = requests.post(
        "https://api.twitter.com/2/oauth2/token",
        data={
            "grant_type": "authorization_code",
            "code": _auth_code,
            "redirect_uri": REDIRECT_URI,
            "code_verifier": code_verifier,
            "client_id": TWITTER_CLIENT_ID,
        },
        auth=(TWITTER_CLIENT_ID, TWITTER_CLIENT_SECRET),
    )
    resp.raise_for_status()
    tokens = resp.json()
    _save_tokens(tokens)
    return tokens["access_token"]


def _get_user_id(access_token: str, username: str) -> str | None:
    resp = requests.get(
        f"https://api.twitter.com/2/users/by/username/{username}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    if resp.status_code == 200:
        return resp.json()["data"]["id"]
    return None


def send_dm(access_token: str, twitter_username: str, maker: dict) -> bool:
    first_name = maker["maker_name"].split()[0]
    message = TWITTER_MESSAGE.format(
        first_name=first_name,
        product_name=maker["product_name"],
        rank=maker["product_rank"],
    )

    user_id = _get_user_id(access_token, twitter_username)
    if not user_id:
        print(f"    Could not resolve user ID for @{twitter_username}")
        return False

    resp = requests.post(
        f"https://api.twitter.com/2/dm_conversations/with/{user_id}/messages",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json={"text": message},
    )

    if resp.status_code in (200, 201):
        return True

    print(f"    Twitter API error {resp.status_code}: {resp.text}")
    return False
