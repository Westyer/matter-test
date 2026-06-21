import os
from dotenv import load_dotenv

load_dotenv()

PRODUCT_HUNT_TOKEN = os.getenv("PRODUCT_HUNT_TOKEN", "")

TARGET_TITLES = [
    "ceo", "chief executive officer",
    "cpo", "chief product officer",
    "co-founder", "cofounder", "founder",
]

MESSAGE = (
    "Hi {first_name},\n\n"
    "Congrats on the recent PH launch and cracking top 10 🎉 Curious how that's "
    "translating into revenue, and what else you're stacking on top of it to keep things rolling.\n\n"
    "We've been talking to founders who are Miro, PayPal, Nvidia, and Higgsfield alums, among others. "
    "Happy to send over a playbook of their best hacks once it's all done, as a thanks for sharing yours.\n\n"
    "Open to a quick 20-min call sometime?"
)
