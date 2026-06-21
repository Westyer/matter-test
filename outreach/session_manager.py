import json
from pathlib import Path
from playwright.sync_api import Browser, BrowserContext

SESSIONS_DIR = Path(__file__).parent / "sessions"
SENT_LOG     = Path(__file__).parent / "sent_log.json"


def load_sent_log() -> set:
    if SENT_LOG.exists():
        with open(SENT_LOG) as f:
            return set(json.load(f))
    return set()


def save_sent_log(sent: set):
    with open(SENT_LOG, "w") as f:
        json.dump(sorted(sent), f, indent=2)


def get_context(browser: Browser, platform: str) -> BrowserContext:
    SESSIONS_DIR.mkdir(exist_ok=True)
    storage = SESSIONS_DIR / f"{platform}_session.json"
    if storage.exists():
        return browser.new_context(storage_state=str(storage))
    return browser.new_context()


def save_context(context: BrowserContext, platform: str):
    SESSIONS_DIR.mkdir(exist_ok=True)
    storage = SESSIONS_DIR / f"{platform}_session.json"
    context.storage_state(path=str(storage))
