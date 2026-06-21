from playwright.sync_api import Page
from config import LINKEDIN_EMAIL, LINKEDIN_PASSWORD, LINKEDIN_MESSAGE


def login_linkedin(page: Page):
    page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
    page.wait_for_timeout(2000)

    if "/feed" in page.url or "/mynetwork" in page.url:
        return  # session already active

    page.fill("#username", LINKEDIN_EMAIL)
    page.fill("#password", LINKEDIN_PASSWORD)
    page.click('button[type="submit"]')
    page.wait_for_url("**/feed/**", timeout=30000)
    page.wait_for_timeout(1500)


def find_linkedin_url(page: Page, ph_profile_url: str) -> str | None:
    """Visit the maker's Product Hunt profile and extract any LinkedIn link."""
    page.goto(ph_profile_url, wait_until="domcontentloaded")
    page.wait_for_timeout(2000)

    for anchor in page.query_selector_all("a[href*='linkedin.com']"):
        href = anchor.get_attribute("href") or ""
        if "linkedin.com/in/" in href:
            return href.split("?")[0]  # strip tracking params
    return None


def send_linkedin_message(page: Page, linkedin_url: str, maker: dict) -> bool:
    first_name = maker["maker_name"].split()[0]
    message = LINKEDIN_MESSAGE.format(
        first_name=first_name,
        product_name=maker["product_name"],
        rank=maker["product_rank"],
    )

    page.goto(linkedin_url, wait_until="domcontentloaded")
    page.wait_for_timeout(2500)

    # "Message" button exists only for 1st-degree connections
    msg_btn = (
        page.query_selector('button[aria-label^="Message"]')
        or page.query_selector('a[aria-label^="Message"]')
    )
    if not msg_btn:
        print(f"    No Message button for {maker['maker_name']} — not a connection yet")
        return False

    msg_btn.click()
    page.wait_for_timeout(2000)

    # Message compose box
    composer = (
        page.query_selector(".msg-form__contenteditable")
        or page.query_selector('[role="textbox"][aria-label*="message"]')
        or page.query_selector('[data-placeholder*="Write a message"]')
    )
    if not composer:
        print(f"    Could not open message composer for {maker['maker_name']}")
        return False

    composer.click()
    composer.fill(message)
    page.wait_for_timeout(500)

    send_btn = (
        page.query_selector(".msg-form__send-button")
        or page.query_selector('button[type="submit"][aria-label*="Send"]')
    )
    if not send_btn:
        print(f"    Could not find Send button for {maker['maker_name']}")
        return False

    send_btn.click()
    page.wait_for_timeout(1500)
    return True
