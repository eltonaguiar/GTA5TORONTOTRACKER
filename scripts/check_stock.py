#!/usr/bin/env python3
"""
Monitor Canada Computers console stock and regenerate README.md.

Runs on a schedule via GitHub Actions (.github/workflows/stock-monitor.yml)
or locally. Parses the per-store stock table embedded in each product page,
then rewrites README.md with two tables:
  Table 1 = VERIFIED (Canada Computers auto-scraped + Amazon browser-verified snapshot)
  Table 2 = UNVERIFIED (bot-walled retailers -> manual check)

If a page can't be fetched it is marked "check failed" -- never a fake "sold out".
"""
import re
import sys
import datetime
from pathlib import Path

try:
    from curl_cffi import requests as cffi_requests
    _HAS_CFFI = True
except Exception:
    _HAS_CFFI = False
import urllib.request

EST = datetime.timezone(datetime.timedelta(hours=-5))

def now_est() -> str:
    return datetime.datetime.now(EST).strftime("%Y-%m-%d %H:%M EST")

def fetch(url: str, timeout: int = 40):
    """Return (status, html). status may be 'ERR:...' on failure."""
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/124.0 Safari/537.36"),
        "Accept-Language": "en-CA,en;q=0.9",
    }
    try:
        if _HAS_CFFI:
            r = cffi_requests.get(url, impersonate="chrome", timeout=timeout, headers=headers)
            return r.status_code, r.text
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except Exception as e:
        return f"ERR:{type(e).__name__}", ""

def parse_cc(html: str):
    """Return (online_qty, {store: qty}, delivery_text)."""
    online = None
    m = re.search(r"<span>\s*Online\s*</span>\s*<span[^>]*>\s*(\d+)\s*</span>", html)
    if m:
        online = int(m.group(1))
    stores = {}
    for name, qty in re.findall(
        r'<span class="col-3[^"]*">\s*([^<]+?)\s*</span>\s*'
        r'<span class="ml-2 shop-online-box[^"]*">\s*(\d+)\s*</span>',
        html,
    ):
        stores[name.strip()] = int(qty)
    delivery = ""
    low = html.lower()
    if "sold out at all locations" in low:
        delivery = "Sold Out at All Locations"
    elif "sold out online" in low:
        delivery = "Sold out online"
    elif "in stock online" in low:
        delivery = "In stock online"
    return online, stores, delivery

# ---- product lists ---------------------------------------------------------
CC_PRODUCTS = [
    ("Xbox Series X 1TB (Black)",
     "https://www.canadacomputers.com/en/xbox/184244/microsoft-xbox-series-x-1tb-black-rrt-00001.html"),
    ("Xbox Series X 1TB Digital (Robot White)",
     "https://www.canadacomputers.com/en/xbox/264257/xbox-series-x-1tb-digital-console-robot-white-ep2-00692.html"),
    ("Xbox Series S 512GB",
     "https://www.canadacomputers.com/en/xbox/184250/microsoft-xbox-series-s-512-gb-all-digital-console-white-rrs-00001.html"),
    ("Xbox Series S 1TB",
     "https://www.canadacomputers.com/en/xbox/264253/microsoft-xbox-series-s-1tb-console-robot-white-ep2-00634.html"),
    ("PS5 Slim (Disc)",
     "https://www.canadacomputers.com/en/playstation/247956/sony-playstation-5-slim-console-1000039655-1000049888.html"),
    ("PS5 Slim Digital 825GB",
     "https://www.canadacomputers.com/en/playstation/247955/sony-playstation-5-slim-console-digital-edition-1000039669-1000049898.html"),
    ("PS5 Pro",
     "https://www.canadacomputers.com/en/playstation/263621/sony-playstation-5-pro-digital-edition-1000046547-1000050805.html"),
]

DOWntown = "Toronto Downtown"
GTA_STORES = {
    "Toronto Downtown", "North York Lawrence", "Etobicoke", "Scarborough",
    "North York Centerpoint Mall", "Mississauga", "Vaughan", "Markham",
    "Richmond Hill", "Brampton", "Oakville", "Ajax", "Burlington", "Whitby",
    "Newmarket", "Oshawa", "Hamilton",
}

# Amazon rows are browser-validated snapshots (delivering to Toronto M5G).
AMAZON_ROWS = [
    ("Xbox Series X 1TB", "$1,299.50", "✅ In Stock",
     "Amazon.ca — FREE delivery Nov 26–27", "https://www.amazon.ca/dp/B0BMXVWSD6", "2026-11-20 16:20"),
    ("Xbox Series S 512GB", "$649.96", "✅ In stock (Add to Cart)",
     "Amazon.ca — delivery Sat Dec 5", "https://www.amazon.ca/dp/B0FLL9VRL5", "2026-11-20 16:20"),
    ("PS5 Digital Edition (Slim)", "$1,099.99", "✅ \"Only 4 left in stock\"",
     "Amazon.ca — delivery Nov 26–27", "https://www.amazon.ca/dp/B0CL7NKBBL", "2026-11-20 16:20"),
]

def build_readme(cc_rows, stamp):
    lines = []
    a = lines.append
    a("# GTA Toronto Console Tracker\n")
    a("In-stock check for **Xbox Series X / S** and **PlayStation 5** for "
      "**downtown Toronto / GTA** (delivery or pickup near M5G).\n")
    a("- **Verified** rows = read in a real browser (Amazon) or scraped from the "
      "product page's embedded stock table (Canada Computers).")
    a("- **Unverified** rows = retailer blocks automated browsers → a human must "
      "confirm (link/phone given).")
    a("- All times **EST**. This file is auto-updated by "
      "`.github/workflows/stock-monitor.yml`.\n")
    a(f"_Last auto-check (Canada Computers): **{stamp}**._\n")
    a("## Table 1 — VERIFIED\n")
    a("| Console | Price | Status | Where / delivery to downtown (M5G) | Link | Last updated (EST) |")
    a("|---|---|---|---|---|---|")
    for r in AMAZON_ROWS:
        a(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]} |")
    for r in cc_rows:
        a(f"| {r['console']} | — | {r['status']} | {r['where']} | {r['link']} | {r['stamp']} |")
    a("")
    a("**How to read it:** a Canada Computers row turns ✅ the moment the store "
      "page shows an online or in-store quantity > 0. Toronto Downtown = 312 "
      "Yonge St; GTA stores (Markham, etc.) count too.\n")
    a("## Table 2 — UNVERIFIED (site blocks bots — manual check required)\n")
    a("| Retailer / Store | What to check | Why unverified | Link / phone | Last checked (EST) |")
    a("|---|---|---|---|---|")
    a("| Best Buy Canada | Xbox Series S in stock online (API); Series X & PS5 sold out online | Akamai \"Access Denied\" to bots | https://www.bestbuy.ca/en-ca/product/xbox-series-s-512gb-console/19422130 | 2026-11-20 16:00 |")
    a("| Best Buy Canada | PS5 Slim / Series X | Akamai block | https://www.bestbuy.ca/en-ca/product/playstation-5-slim-1tb-console/19446111 | 2026-11-20 16:00 |")
    a("| EB Games / GameStop (267 Yonge St) | PS5 / Xbox store stock | Cloudflare; gamestop.ca does not resolve | https://www.ebgames.ca/ | 2026-11-20 16:00 |")
    a("| Walmart Canada | Consoles | \"Forbidden\" bot block | https://www.walmart.ca/en/search?q=playstation+5 | 2026-11-20 16:00 |")
    a("| Staples | Consoles | Cloudflare challenge | https://www.staples.ca/search?query=playstation+5 | 2026-11-20 16:00 |")
    a("| Memory Express | Consoles | Cloudflare challenge | https://www.memoryexpress.com/ | 2026-11-20 16:00 |")
    a("| Gamerama (local) | Xbox/PS5 shelf stock | Phone verify | 2470 Yonge St — 416-487-8802 | 2026-11-20 16:00 |")
    a("| Queen East Appliance Centre (local) | Consoles | Phone verify | 1180 Queen St E — 416-463-6551 | 2026-11-20 16:00 |")
    a("| ReserveRoom.ca (local) | PS5/Xbox stock | Phone verify | +1 647-809-5721 | 2026-11-20 16:00 |")
    a("| Buy & Sell Kings (local) | New/used consoles | Phone verify | 2852 Danforth Ave — 647-348-1763 | 2026-11-20 16:00 |")
    a("")
    a("## Notes")
    a("- Canada Computers \"Toronto Downtown\" = 312 Yonge Street, Toronto, ON M5B 1R4.")
    a("- Auto-monitor covers Canada Computers (server-rendered stock table). "
      "Amazon rows are a manual browser snapshot. Bot-walled retailers need a human.")
    a("- Run locally: `python scripts/check_stock.py` (install `curl_cffi`). "
      "Cron example: `*/30 * * * * cd /path/repo && python scripts/check_stock.py && git commit -am auto && git push`.")
    a("")
    return "\n".join(lines)

def main():
    rows = []
    for console, url in CC_PRODUCTS:
        status_code, html = fetch(url)
        if isinstance(status_code, int) and status_code == 200 and html:
            online, stores, delivery = parse_cc(html)
            in_stock_stores = {k: v for k, v in stores.items() if v > 0}
            gta = {k: v for k, v in in_stock_stores.items() if k in GTA_STORES}
            if online and online > 0:
                status = f"✅ In stock online ({online})"
                where = "Canada Computers — online"
            elif in_stock_stores:
                status = "✅ In store"
                where = "Canada Computers — " + ", ".join(f"{k}: {v}" for k, v in in_stock_stores.items())
            else:
                status = "⛔ Sold out (online + all stores)"
                where = "Canada Computers — sold out online + all locations"
            if gta and not (online and online > 0):
                where += " | GTA: " + ", ".join(f"{k}:{v}" for k, v in gta.items())
            print(f"[OK] {console}: online={online} stores_with_stock={in_stock_stores}")
        else:
            status = f"⚠️ check failed ({status_code}) — verify manually"
            where = "Canada Computers — could not fetch automatically"
            print(f"[FAIL] {console}: {status_code}")
        rows.append({"console": console, "status": status, "where": where,
                     "link": url, "stamp": now_est()})

    stamp = now_est()
    readme = build_readme(rows, stamp)
    out = Path(__file__).resolve().parent.parent / "README.md"
    out.write_text(readme, encoding="utf-8")
    print(f"\nWrote {out}")

if __name__ == "__main__":
    main()
