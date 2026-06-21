import os
from dotenv import load_dotenv

load_dotenv()

PRODUCT_HUNT_TOKEN = os.getenv("PRODUCT_HUNT_TOKEN", "")
TWITTER_USERNAME   = os.getenv("TWITTER_USERNAME", "")
TWITTER_PASSWORD   = os.getenv("TWITTER_PASSWORD", "")
LINKEDIN_EMAIL     = os.getenv("LINKEDIN_EMAIL", "")
LINKEDIN_PASSWORD  = os.getenv("LINKEDIN_PASSWORD", "")

TARGET_TITLES = [
    "ceo", "chief executive officer",
    "cpo", "chief product officer",
    "co-founder", "cofounder", "founder",
]

TWITTER_MESSAGE = (
    "Hey {first_name} 👋 Saw {product_name} hit #{rank} on Product Hunt today — "
    "congrats on the launch! Always love seeing what founders are shipping. "
    "Would love to connect and swap notes if you're open to it."
)

LINKEDIN_MESSAGE = (
    "Hi {first_name},\n\n"
    "Saw {product_name} trending on Product Hunt today — impressive launch!\n\n"
    "I'm always looking to connect with founders and product leaders building "
    "interesting things. Would love to learn more about what you're working on "
    "and see if there's a way we can be useful to each other.\n\n"
    "Open to a quick chat?"
)
