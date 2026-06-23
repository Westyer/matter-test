#!/usr/bin/env python3
"""
Fetches today's top 10 Product Hunt products, finds CEO/CPO/Founder makers,
scrapes their Twitter and LinkedIn profiles, and exports to an Excel file.
"""
import sys
import time
from datetime import date
from pathlib import Path

import requests
from bs4 import BeautifulSoup
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

from config import PRODUCT_HUNT_CLIENT_ID, PRODUCT_HUNT_CLIENT_SECRET, MESSAGE
from product_hunt import get_top_products, filter_target_makers


def validate_config():
    if not PRODUCT_HUNT_CLIENT_ID or not PRODUCT_HUNT_CLIENT_SECRET:
        print("Missing PRODUCT_HUNT_CLIENT_ID or PRODUCT_HUNT_CLIENT_SECRET in .env")
        sys.exit(1)


def get_linkedin_from_ph(username: str) -> str:
    """Scrape the maker's Product Hunt profile for a LinkedIn link."""
    try:
        url = f"https://www.producthunt.com/@{username}"
        resp = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
        if resp.status_code != 200:
            return ""
        soup = BeautifulSoup(resp.text, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "linkedin.com/in/" in href:
                return href.split("?")[0]
    except Exception:
        pass
    return ""


def build_excel(targets: list, output_path: Path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "PH Outreach"

    # Header style
    header_fill = PatternFill("solid", fgColor="1A1A2E")
    header_font = Font(color="FFFFFF", bold=True, size=11)

    headers = ["#", "Product", "Maker", "Title", "Twitter", "LinkedIn", "PH Profile", "Message"]
    col_widths = [4, 22, 20, 28, 28, 40, 32, 60]

    for col, (header, width) in enumerate(zip(headers, col_widths), start=1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.column_dimensions[get_column_letter(col)].width = width

    ws.row_dimensions[1].height = 22

    # Row style alternating
    fill_even = PatternFill("solid", fgColor="F5F5F5")

    for row_idx, t in enumerate(targets, start=2):
        fill = fill_even if row_idx % 2 == 0 else None

        twitter_url = (
            f"https://x.com/{t['twitter_username']}" if t.get("twitter_username") else ""
        )
        first_name = t["maker_name"].split()[0]
        message = MESSAGE.format(first_name=first_name)

        values = [
            t["product_rank"],
            t["product_name"],
            t["maker_name"],
            t["headline"],
            twitter_url,
            t.get("linkedin_url", ""),
            t["ph_profile_url"],
            message,
        ]

        for col, value in enumerate(values, start=1):
            cell = ws.cell(row=row_idx, column=col, value=value)
            cell.alignment = Alignment(wrap_text=(col == len(headers)), vertical="top")
            if fill:
                cell.fill = fill

        ws.row_dimensions[row_idx].height = 80 if t.get("linkedin_url") else 40

    # Freeze header row
    ws.freeze_panes = "A2"

    wb.save(output_path)


def run():
    validate_config()

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

    print("\nScraping LinkedIn profiles from Product Hunt...")
    for t in targets:
        print(f"  Checking @{t['maker_username']}...")
        t["linkedin_url"] = get_linkedin_from_ph(t["maker_username"])
        if t["linkedin_url"]:
            print(f"    ✓ {t['linkedin_url']}")
        else:
            print(f"    — no LinkedIn found")
        time.sleep(0.5)  # be polite to PH servers

    output = Path(__file__).parent / f"outreach_{date.today()}.xlsx"
    build_excel(targets, output)
    print(f"\nExcel saved to: {output}")


if __name__ == "__main__":
    run()
