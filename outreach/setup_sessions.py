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
from pathlib import Path
from playwright.sync_api import sync_playwright

SESSIONS_DIR = Path(__file__).parent / "sessions"

CHROME_PROFILE = Path(os.path.expanduser(
    "~/Library/Application Support/Google/Chrome"
))


def check_chrome_closed():
    import subprocess
    result = subprocess.run(
        ["pgrep", "-x", "Google Chrome"], capture_output=True
    )
    if result.returncode == 0:
        print("Chrome is still running. Please quit Chrome fully (Cmd+Q) and try again.")
        sys.exit(1)


def export_platform(platform: str, url: str, logged_in_check: str):
    dest = SESSIONS_DIR / f"chrome_{platform}"

    # Copy Chrome Default profile to our sessions dir
    src = CHROME_PROFILE / "Default"
    if dest.exists():
        shutil.rmtree(dest)
    print(f"  Copying Chrome profile for {platform}...")
    shutil.copytree(src, dest, ignore=shutil.ignore_patterns(
        "Cache", "Code Cache", "GPUCache", "DawnCache",
        "ShaderCache", "*.log", "CrashpadMetrics*",
    ))

    # Verify the session is active
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            str(dest), channel="chrome", headless=False
        )
        page = ctx.new_page()
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        if logged_in_check in page.url or page.query_selector(logged_in_check):
            print(f"  ✓ {platform.capitalize()} session confirmed")
        else:
            print(f"  ✗ Not logged into {platform.capitalize()} in Chrome.")
            print(f"    Open Chrome, log in at {url}, then re-run this script.")

        ctx.close()


if __name__ == "__main__":
    print("Checking Chrome is closed...")
    check_chrome_closed()

    SESSIONS_DIR.mkdir(exist_ok=True)

    print("\nExporting Twitter session...")
    export_platform("twitter", "https://x.com/home", "home")

    print("\nExporting LinkedIn session...")
    export_platform("linkedin", "https://www.linkedin.com/feed/", "feed")

    print("\nDone! Run python3 main.py to start outreach.")
