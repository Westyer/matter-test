#!/usr/bin/env python3
"""
One-time setup: exports your Twitter and LinkedIn sessions from your
existing Chrome browser so main.py can reuse them without logging in.

Before running:
  1. Make sure you are logged into Twitter and LinkedIn in Chrome
  2. Close Chrome completely (Cmd+Q, not just the window)
  3. Run: python3 setup_sessions.py
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright

SESSIONS_DIR = Path(__file__).parent / "sessions"

POSSIBLE_CHROME_PATHS = [
    "~/Library/Application Support/Google/Chrome",
    "~/Library/Application Support/Google/Chrome Canary",
    "~/Library/Application Support/BraveSoftware/Brave-Browser",
    "~/Library/Application Support/Microsoft Edge",
]


def find_chrome_profile() -> Path:
    for p in POSSIBLE_CHROME_PATHS:
        base = Path(os.path.expanduser(p))
        default = base / "Default"
        if default.exists():
            print(f"  Found profile: {base}")
            return base
        if base.exists():
            for child in sorted(base.iterdir()):
                if (child / "Cookies").exists():
                    print(f"  Found profile: {base}")
                    return base
    print("Could not find a Chrome/Brave/Edge profile. Paths checked:")
    for p in POSSIBLE_CHROME_PATHS:
        print(f"  {p}")
    sys.exit(1)


def check_browser_closed():
    for name in ["Google Chrome", "Brave Browser", "Microsoft Edge"]:
        result = subprocess.run(["pgrep", "-x", name], capture_output=True)
        if result.returncode == 0:
            print(f"{name} is still running. Please quit it fully (Cmd+Q) and try again.")
            sys.exit(1)


def export_platform(chrome_base: Path, platform: str, url: str, logged_in_url_fragment: str):
    dest = SESSIONS_DIR / f"chrome_{platform}"
    src = chrome_base / "Default"
    if not src.exists():
        src = chrome_base

    if dest.exists():
        shutil.rmtree(dest)

    print(f"  Copying profile for {platform}...")
    shutil.copytree(src, dest, ignore=shutil.ignore_patterns(
        "Cache", "Code Cache", "GPUCache", "DawnCache",
        "ShaderCache", "*.log", "CrashpadMetrics*",
    ))

    print(f"  Verifying {platform} session...")
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            str(dest),
            channel="chrome",
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
            ignore_default_args=["--enable-automation"],
        )
        page = ctx.new_page()
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        if logged_in_url_fragment in page.url:
            print(f"  ✓ {platform.capitalize()} session active")
        else:
            print(f"  ✗ Not logged in to {platform.capitalize()}.")
            print(f"    Log in at {url} in your browser, then re-run this script.")

        ctx.close()


if __name__ == "__main__":
    print("Checking browser is closed...")
    check_browser_closed()

    chrome_base = find_chrome_profile()
    SESSIONS_DIR.mkdir(exist_ok=True)

    print("\nExporting Twitter session...")
    export_platform(chrome_base, "twitter", "https://x.com/home", "home")

    print("\nExporting LinkedIn session...")
    export_platform(chrome_base, "linkedin", "https://www.linkedin.com/feed/", "feed")

    print("\nDone! Run python3 main.py to start outreach.")
