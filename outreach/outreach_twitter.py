from playwright.sync_api import Page
from config import MESSAGE


def login_twitter(page: Page):
    """Open X and wait for the user to log in manually in the browser."""
    page.goto("https://x.com/login", wait_until="domcontentloaded")
    page.wait_for_timeout(2000)

    if "home" in page.url:
        return  # already logged in from saved session

    print("  Twitter/X: Please log in in the browser window that just opened.")
    print("  Waiting up to 2 minutes for you to complete login...")
    page.wait_for_url("**/home", timeout=120000)
    print("  Twitter login detected — session saved for next run.")


def send_dm(page: Page, twitter_username: str, maker: dict) -> bool:
    first_name = maker["maker_name"].split()[0]
    message = MESSAGE.format(first_name=first_name)

    page.goto(f"https://x.com/{twitter_username}", wait_until="domcontentloaded")
    page.wait_for_timeout(2500)

    dm_btn = page.query_selector('[data-testid="sendDMFromProfile"]')
    if not dm_btn:
        print(f"    No DM button for @{twitter_username} — DMs may be disabled")
        return False

    dm_btn.click()
    page.wait_for_timeout(2000)

    composer = page.query_selector('[data-testid="dmComposerTextInput"]')
    if not composer:
        print(f"    Could not open DM composer for @{twitter_username}")
        return False

    composer.click()
    composer.fill(message)
    page.wait_for_timeout(500)

    send_btn = page.query_selector('[data-testid="dmComposerSendButton"]')
    if send_btn:
        send_btn.click()
    else:
        page.keyboard.press("Enter")

    page.wait_for_timeout(1500)
    return True
