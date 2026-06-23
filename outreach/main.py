#!/usr/bin/env python3
"""
Product Hunt outreach script.
Fetches today's top 10 PH products, finds CEO/CPO/Founder makers,
and sends them a message on Twitter and LinkedIn.
Both platforms use persistent Chrome profiles — log in once, reused after.
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

from config import PRODUCT_HUNT_CLIENT_ID, PRODUCT_HUNT_CLIENT_SECRET
from product_hunt import get_top_products, filter_target_makers
from session_manager import load_sent_log, save_sent_log
from outreach_twitter import login_twitter, send_dm
from outreach_linkedin import login_linkedin, find_linkedin_url, send_linkedin_message

PROFILES_DIR = Path(__file__).parent / "sessions"


def validate_config():
    if not PRODUCT_HUNT_CLIENT_ID or not PRODUCT_HUNT_CLIENT_SECRET:
        print("Missing PRODUCT_HUNT_CLIENT_ID or PRODUCT_HUNT_CLIENT_SECRET in .env")
        sys.exit(1)


def run():
    validate_config()
    sent_log = load_sent_log()

    print("Fetching today's top 10 Product Hunt products...")
    products = get_top_products()
    print(f"Found {len(products)} products.")

    targets = filter_target_makers(products)
    if not targets:
        print("No CEO/CPO/Founder makers found today. Try again later.")
        return

    print(f"Found {len(targets)} target maker(s):\n")
    for t in targets:
        print(f"  #{t['product_rank']} {t['product_name']} — {t['maker_name']} ({t['headline']})")
    print()

    with sync_playwright() as p:

        # ── Twitter ───────────────────────────────────────────────────────────
        twitter_targets = [t for t in targets if t.get("twitter_username")]
        print(f"=== Twitter ({len(twitter_targets)} targets) ===")

        if twitter_targets:
            tw_profile = PROFILES_DIR / "chrome_twitter"
            tw_profile.mkdir(parents=True, exist_ok=True)
            tw_ctx = p.chromium.launch_persistent_context(
                str(tw_profile),
                channel="chrome",
                headless=False,
                args=["--disable-blink-features=AutomationControlled"],
                ignore_default_args=["--enable-automation"],
            )
            tw_page = tw_ctx.new_page()
            login_twitter(tw_page)

            for maker in twitter_targets:
                handle = maker["twitter_username"]
                key = f"twitter:{handle}"
                if key in sent_log:
                    print(f"  ↩  @{handle} already messaged, skipping")
                    continue
                print(f"  → DM to @{handle} ({maker['maker_name']}) re: {maker['product_name']} ...")
                if send_dm(tw_page, handle, maker):
                    sent_log.add(key)
                    save_sent_log(sent_log)
                    print("     ✓ sent")

            tw_ctx.close()
        else:
            print("  No makers with a Twitter handle found.")

        # ── LinkedIn ──────────────────────────────────────────────────────────
        print(f"\n=== LinkedIn ({len(targets)} targets to check) ===")

        li_profile = PROFILES_DIR / "chrome_linkedin"
        li_profile.mkdir(parents=True, exist_ok=True)
        li_ctx = p.chromium.launch_persistent_context(
            str(li_profile),
            channel="chrome",
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
            ignore_default_args=["--enable-automation"],
        )
        li_page = li_ctx.new_page()
        login_linkedin(li_page)

        for maker in targets:
            print(f"  Checking PH profile for {maker['maker_name']} ...")
            linkedin_url = find_linkedin_url(li_page, maker["ph_profile_url"])
            if not linkedin_url:
                print("    No LinkedIn link found on PH profile")
                continue

            key = f"linkedin:{linkedin_url}"
            if key in sent_log:
                print("    ↩  Already messaged on LinkedIn, skipping")
                continue

            print(f"    → Message to {maker['maker_name']} re: {maker['product_name']} ...")
            if send_linkedin_message(li_page, linkedin_url, maker):
                sent_log.add(key)
                save_sent_log(sent_log)
                print("       ✓ sent")

        li_ctx.close()

    print("\nAll done! Results saved to sent_log.json")


if __name__ == "__main__":
    run()
