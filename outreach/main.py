#!/usr/bin/env python3
"""
Fetches Product Hunt top 10 products for a date range, finds CEO/CPO/Founder
makers, scrapes their Twitter and LinkedIn profiles, and exports to Excel.

Usage:
  python3 main.py                        # today only
  python3 main.py 2026-06-01 2026-06-23  # date range
"""
import sys
import time
from datetime import date, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

from config import PRODUCT_HUNT_CLIENT_ID, PRODUCT_HUNT_CLIENT_SECRET, MESSAGE
from product_hunt import get_access_token, get_top_products_for_date, filter_target_makers


def validate_config():
    if not PRODUCT_HUNT_CLIENT_ID or not PRODUCT_HUNT_CLIENT_SECRET:
        print("Missing PRODUCT_HUNT_CLIENT_ID or PRODUCT_HUNT_CLIENT_SECRET in .env")
        sys.exit(1)


def date_range(start: date, end: date):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def get_linkedin_from_ph(username: str) -> str:
    try:
        resp = requests.get(
            f"https://www.producthunt.com/@{username}",
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

    header_fill = PatternFill("solid", fgColor="1A1A2E")
    header_font = Font(color="FFFFFF", bold=True, size=11)

    headers    = ["Date", "#", "Product", "Maker", "Title", "Twitter", "LinkedIn", "PH Profile", "Message"]
    col_widths = [13,     4,   22,        20,       28,      35,        40,          32,           65]

    for col, (header, width) in enumerate(zip(headers, col_widths), start=1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.column_dimensions[get_column_letter(col)].width = width

    ws.row_dimensions[1].height = 22
    fill_even = PatternFill("solid", fgColor="F5F5F5")

    for row_idx, t in enumerate(targets, start=2):
        row_fill = fill_even if row_idx % 2 == 0 else None
        twitter_url = f"https://x.com/{t['twitter_username']}" if t.get("twitter_username") else ""
        first_name  = t["maker_name"].split()[0]
        message     = MESSAGE.format(first_name=first_name)

        values = [
            t["date"], t["product_rank"], t["product_name"],
            t["maker_name"], t["headline"],
            twitter_url, t.get("linkedin_url", ""),
            t["ph_profile_url"], message,
        ]

        for col, value in enumerate(values, start=1):
            cell = ws.cell(row=row_idx, column=col, value=value)
            cell.alignment = Alignment(wrap_text=(col == len(headers)), vertical="top")
            if row_fill:
                cell.fill = row_fill

        ws.row_dimensions[row_idx].height = 100

    ws.freeze_panes = "A2"
    wb.save(output_path)


def run(start_date: date, end_date: date):
    validate_config()

    print(f"Fetching Product Hunt data from {start_date} to {end_date}...")
    token = get_access_token()

    all_targets = []
    days = list(date_range(start_date, end_date))

    for day in days:
        print(f"  {day} ...", end=" ", flush=True)
        try:
            products = get_top_products_for_date(token, day)
            targets  = filter_target_makers(products, day)
            all_targets.extend(targets)
            print(f"{len(targets)} target(s)")
        except Exception as e:
            print(f"error: {e}")
        time.sleep(0.5)

    if not all_targets:
        print("No targets found.")
        return

    print(f"\nTotal targets: {len(all_targets)}")
    print("Scraping LinkedIn profiles from Product Hunt...")

    seen_usernames = {}
    for t in all_targets:
        u = t["maker_username"]
        if u in seen_usernames:
            t["linkedin_url"] = seen_usernames[u]
            continue
        linkedin = get_linkedin_from_ph(u)
        t["linkedin_url"] = linkedin
        seen_usernames[u] = linkedin
        status = f"✓ {linkedin}" if linkedin else "— not found"
        print(f"  @{u}: {status}")
        time.sleep(0.5)

    label = f"{start_date}_to_{end_date}" if start_date != end_date else str(start_date)
    output = Path(__file__).parent / f"outreach_{label}.xlsx"
    build_excel(all_targets, output)
    print(f"\nExcel saved to: {output}")


if __name__ == "__main__":
    if len(sys.argv) == 3:
        start = date.fromisoformat(sys.argv[1])
        end   = date.fromisoformat(sys.argv[2])
    else:
        start = end = date.today()

    run(start, end)
