#!/usr/bin/env python3
"""
Product Hunt outreach script.
Fetches today's top 10 PH products, finds CEO/CPO/Founder makers,
and sends them a message on Twitter and LinkedIn.
Both platforms use browser sessions — log in once, reused after.
"""
import sys
from playwright.sync_api import sync_playwright

from config import PRODUCT_HUNT_CLIENT_ID, PRODUCT_HUNT_CLIENT_SECRET
from product_hunt import get_top_products, filter_target_makers
from session_manager import get_context, save_context, load_sent_log, save_sent_log
from outreach_twitter import login_twitter, send_dm
from outreach_linkedin import login_linkedin, find_linkedin_url, send_linkedin_message


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
        browser = p.chromium.launch(headless=False, channel="chrome")

        # ── Twitter ───────────────────────────────────────────────────────────
        twitter_targets = [t for t in targets if t.get("twitter_username")]
        print(f"=== Twitter ({len(twitter_targets)} targets) ===")

        if twitter_targets:
            tw_ctx  = get_context(browser, "twitter")
            tw_page = tw_ctx.new_page()
            login_twitter(tw_page)
            save_context(tw_ctx, "twitter")

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

        li_ctx  = get_context(browser, "linkedin")
        li_page = li_ctx.new_page()
        login_linkedin(li_page)
        save_context(li_ctx, "linkedin")

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
        browser.close()

    print("\nAll done! Results saved to sent_log.json")


if __name__ == "__main__":
    run()
