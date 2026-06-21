from playwright.sync_api import Page
from config import TWITTER_USERNAME, TWITTER_PASSWORD, TWITTER_MESSAGE


def login_twitter(page: Page):
    page.goto("https://x.com/login", wait_until="domcontentloaded")
    page.wait_for_timeout(2000)

    if "home" in page.url:
        return  # session already active

    # Step 1: username / email
    username_input = page.wait_for_selector('input[autocomplete="username"]', timeout=10000)
    username_input.fill(TWITTER_USERNAME)
    page.keyboard.press("Enter")
    page.wait_for_timeout(2000)

    # Step 2: unusual activity gate (asks for phone or username again)
    unusual = page.query_selector('input[data-testid="ocfEnterTextTextInput"]')
    if unusual:
        unusual.fill(TWITTER_USERNAME)
        page.keyboard.press("Enter")
        page.wait_for_timeout(2000)

    # Step 3: password
    password_input = page.wait_for_selector('input[name="password"]', timeout=10000)
    password_input.fill(TWITTER_PASSWORD)
    page.keyboard.press("Enter")
    page.wait_for_url("**/home", timeout=30000)


def send_dm(page: Page, twitter_username: str, maker: dict) -> bool:
    first_name = maker["maker_name"].split()[0]
    message = TWITTER_MESSAGE.format(
        first_name=first_name,
        product_name=maker["product_name"],
        rank=maker["product_rank"],
    )

    page.goto(f"https://x.com/{twitter_username}", wait_until="domcontentloaded")
    page.wait_for_timeout(2500)

    dm_button = page.query_selector('[data-testid="sendDMFromProfile"]')
    if not dm_button:
        print(f"    No DM button for @{twitter_username} — DMs may be disabled")
        return False

    dm_button.click()
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
