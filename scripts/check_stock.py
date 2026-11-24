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
import json
import datetime
import urllib.parse
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


# ---------------------------------------------------------------- live first-party JSON sources
# Both of these are real JSON endpoints that answer 200 to a normal client -- they are NOT
# bot-walled, contrary to what Table 2 used to claim. Verified 2026-11-24.
BBY_SKUS = [
    ("Xbox Series S 512GB", "19422130"),
    ("PS5 Slim 1TB", "19446111"),
    ("PS5 Slim Disc Edition", "19609594"),
    ("PS5 Pro 2TB (open box)", "20351327"),
]
BBY_API = ("https://www.bestbuy.ca/ecomm-api/availability/products"
           "?accept-language=en-CA&postalCode=M5G&skus={skus}&quantities=1")


def fetch_bestbuy():
    """Live availability from Best Buy's own JSON API. sellerId=bbyca means first-party stock.

    NOTE: the endpoint rejects a comma-joined `skus` list with HTTP 412
    ("Invalid query parameter: getProductAvailability.skus"), so each SKU needs its own
    request. 412 here is a schema error, not an anti-bot block -- do not "fix" it with a browser.
    """
    out = []
    for name, sku in BBY_SKUS:
        status, body = fetch(BBY_API.format(skus=sku))
        if not (isinstance(status, int) and status == 200 and body):
            print(f"[FAIL] bestbuy {sku}: {status}")
            continue
        try:
            data = json.loads(body)
        except Exception as e:
            print(f"[FAIL] bestbuy parse {sku}: {e}")
            continue
        avail = data.get("availabilities") or []
        a = avail[0] if avail else None
        if not a:
            continue
        ship = (a.get("shipping") or {}).get("status", "?")
        pick = (a.get("pickup") or {}).get("status", "?")
        seller = a.get("sellerId") or "?"
        ok = ship == "InStock"
        out.append({"name": name, "price": "—",
                    "status": ("✅ " if ok else "❌ ") + f"online {ship} · pickup {pick}",
                    "where": f"Best Buy Canada ({seller})",
                    "link": f"https://www.bestbuy.ca/en-ca/product/{sku}",
                    "stamp": now_est()})
        print(f"[OK] bestbuy {name}: ship={ship} pick={pick} seller={seller}")
    return out


STAPLES_QUERIES = ["playstation 5", "xbox series x"]


def fetch_staples():
    """Staples CA runs on Shopify, so its suggest.json is a public product feed."""
    out = []
    for q in STAPLES_QUERIES:
        params = urllib.parse.urlencode({"q": q, "resources[type]": "product",
                                        "resources[limit]": "6"})
        status, body = fetch(f"https://www.staples.ca/search/suggest.json?{params}")
        if not (isinstance(status, int) and status == 200 and body):
            print(f"[FAIL] staples {q}: {status}")
            continue
        try:
            prods = (json.loads(body).get("resources", {}).get("results", {})
                     .get("products", []))
        except Exception as e:
            print(f"[FAIL] staples parse {q}: {e}")
            continue
        for p in prods:
            price = p.get("price")
            avail = str(p.get("available", "")).strip().lower()
            ok = avail not in ("", "0", "false")
            url = p.get("url") or ""
            out.append({"name": str(p.get("title", ""))[:90],
                        "price": f"${price}" if price else "—",
                        "status": ("✅ " if ok else "❌ ") + ("available online" if ok else "unavailable"),
                        "where": "Staples Canada",
                        "link": ("https://www.staples.ca" + url) if url.startswith("/") else url,
                        "stamp": now_est()})
        print(f"[OK] staples {q}: {len(prods)} products")
    return out




# ---------------------------------------------------------------- GitHub Pages data feed
# One JSON file drives the filterable table. Other agents append rows here; `owner` says who
# owns the row so parallel work never silently overwrites a source.
WALMART_OBS = [
    ("PlayStation 5 Digital Edition - 825 GB", 1899.00, "BuySmart", "marketplace",
     "https://www.walmart.ca/en/search?q=playstation+5",
     "Observed 2026-11-24 via headful real Chrome. Marketplace reseller, not first-party."),
    ("PlayStation 5 Pro Console", 2849.99, "always innovating", "marketplace",
     "https://www.walmart.ca/en/search?q=playstation+5",
     "Observed 2026-11-24 via headful real Chrome. Marketplace reseller, not first-party."),
    ("Saros (PlayStation 5)", 49.96, "Walmart.ca", "first-party",
     "https://www.walmart.ca/en/search?q=playstation+5",
     "Observed 2026-11-24 via headful real Chrome."),
]

PLACEHOLDERS = [
    ("GameStop / EB Games", "PS5 + Xbox store stock (267 Yonge St)", "agent: gamestop",
     "gamestop.ca does not resolve from automation; needs manual or in-store check"),
    ("Memory Express", "PS5 + Xbox online stock", "agent: memexpress",
     "search API returns 403 under curl_cffi, Playwright, nodriver and patchright - needs a data-endpoint hunt"),
    ("Amazon.ca", "PS5 / Xbox listing status", "agent: amazon",
     "HTML answers 200 to plain curl; needs the product-level parse wired in"),
    ("Canada Computers (in-store)", "Per-store shelf counts", "auto: cc",
     "covered by Table 1 above; this row is the site placeholder for store-level depth"),
    ("Local shops (Gamerama, Queen East, ReserveRoom, Buy & Sell Kings)", "Phone-verified shelf stock", "agent: local",
     "phone verify only"),
]


def build_site_data(cc_rows, live_rows, stamp):
    """Emit the single table the Pages site renders."""
    rows = []

    for r in live_rows:
        retailer = "Best Buy" if "Best Buy" in r["where"] else "Staples"
        status = "in_stock" if r["status"].startswith("\u2705") else "sold_out"
        seller = ""
        if "(" in r["where"] and ")" in r["where"]:
            seller = r["where"].split("(", 1)[1].rstrip(")")
        price = None
        pt = str(r["price"]).replace("$", "").replace(",", "").strip()
        try:
            price = float(pt)
        except Exception:
            price = None
        rows.append({"retailer": retailer, "product": r["name"], "price": price,
                     "price_text": r["price"], "status": status,
                     "status_text": r["status"].replace("\u2705 ", "").replace("\u274c ", ""),
                     "seller": seller or retailer,
                     "kind": "first-party" if seller in ("", "bbyca", "Staples Canada") else "marketplace",
                     "checked": r["stamp"], "url": r["link"], "method": "json-api", "owner": "auto"})

    for r in cc_rows:
        st = "in_stock" if r["status"].startswith("\u2705") else (
            "sold_out" if r["status"].startswith("\u26d4") else "unknown")
        rows.append({"retailer": "Canada Computers", "product": r["console"], "price": None,
                     "price_text": "-", "status": st,
                     "status_text": r["status"].replace("\u2705 ", "").replace("\u26d4 ", "").replace("\u26a0\ufe0f ", ""),
                     "seller": "Canada Computers", "kind": "first-party",
                     "checked": r["stamp"], "url": r["link"], "method": "page-scrape", "owner": "auto"})

    for name, price, seller, kind, url, note in WALMART_OBS:
        rows.append({"retailer": "Walmart", "product": name, "price": price,
                     "price_text": f"${price:,.2f}", "status": "in_stock",
                     "status_text": "listed", "seller": seller, "kind": kind,
                     "checked": "2026-11-24 09:00 EST", "url": url,
                     "method": "headful-chrome", "owner": "hermes", "note": note})

    for retailer, product, owner, note in PLACEHOLDERS:
        rows.append({"retailer": retailer, "product": product, "price": None, "price_text": "-",
                     "status": "pending", "status_text": "PENDING", "seller": "",
                     "kind": "", "checked": "", "url": "", "method": "", "owner": owner,
                     "note": note})

    return {"generated": stamp, "rows": rows,
            "legend": {"in_stock": "available to buy", "sold_out": "out of stock",
                       "pending": "unclaimed - an agent should fill this", "unknown": "check failed"}}


def build_readme(cc_rows, stamp, live_rows=None):
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
    if live_rows:
        a("## ✅ LIVE VERIFIED — auto-checked this run (newest first)\n")
        a(f"_Fetched **{stamp}** from first-party JSON APIs: Best Buy `ecomm-api` and "
          "Staples Shopify `suggest.json`. Real API responses, not scraping guesses. "
          "`sellerId: bbyca` = Best Buy's own stock, not a marketplace reseller._\n")
        a("| Console | Price | Status | Where | Link | Checked (EST) |")
        a("|---|---|---|---|---|---|")
        for r in live_rows:
            a(f"| {r['name']} | {r['price']} | {r['status']} | {r['where']} | {r['link']} | {r['stamp']} |")
        a("")
    a("## AVAILABLE NOW — user-reported (manual entries, preserved across runs)\n")
    a("> :warning: Reported by a person, not verified by this tracker. Stock changes hourly "
      "— confirm on the page before buying.\n")
    a("| Item | Status | Link |")
    a("|---|---|---|")
    a("| PlayStation 5 Slim Disc Edition | Reported available online | https://www.bestbuy.ca/en-ca/product/playstation-5-disc-edition-console-slim/19609594 |")
    a("| PlayStation 5 Pro 2TB SSD | Reported available — **open box** (check condition grade + warranty) | https://www.bestbuy.ca/en-ca/product/playstation-5-pro-console-with-2tb-ssd-ai-enhanced-4k-resolution-playstation-spectral-super-resolution-open-box/20351327 |")
    a("")
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
    a("| Best Buy Canada | **NOW AUTO-VERIFIED** — see LIVE VERIFIED above | HTML is Akamai-walled, but the `ecomm-api` JSON endpoint answers 200 (verified 2026-11-24) | https://www.bestbuy.ca/en-ca/product/xbox-series-s-512gb-console/19422130 | auto |")
    a("| Best Buy Canada | PS5 Slim 1TB | `ecomm-api` reports online status directly | https://www.bestbuy.ca/en-ca/product/playstation-5-slim-1tb-console/19446111 | auto |")
    a("| EB Games / GameStop (267 Yonge St) | PS5 / Xbox store stock | Cloudflare; gamestop.ca does not resolve | https://www.ebgames.ca/ | 2026-11-20 16:00 |")
    a("| Walmart Canada | Consoles — **marketplace resellers list PS5 at $1899+ (seller BuySmart) vs $1099.99 first-party elsewhere**. Do not buy without checking the seller field | plain HTTP + every known JSON API 403s; a headful real Chrome does load search results, but prices are mostly reseller markup | https://www.walmart.ca/en/search?q=playstation+5 | 2026-11-24 09:00 |")
    a("| Staples | **NOW AUTO-VERIFIED** — see LIVE VERIFIED above | Site is Shopify; `search/suggest.json` returns clean product JSON (verified 2026-11-24) | https://www.staples.ca/search?query=playstation+5 | auto |")
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

    # Live first-party JSON sources. Wrapped so a dead endpoint can never break the
    # Canada Computers path or block the commit.
    live_rows = []
    for fn in (fetch_bestbuy, fetch_staples):
        try:
            live_rows += fn()
        except Exception as e:
            print(f"[FAIL] {fn.__name__}: {e}")

    readme = build_readme(rows, stamp, live_rows)

    # Pages data feed -- best effort, never blocks the README commit
    try:
        import os
        site_dir = Path(__file__).resolve().parent.parent / "docs"
        site_dir.mkdir(exist_ok=True)
        data_path = site_dir / "data.json"
        fresh = build_site_data(rows, live_rows, stamp)

        # Carry forward retailers that returned nothing this run. A CI runner's IP sometimes
        # gets refused by one source; silently dropping that retailer makes the table look
        # like the stock vanished, which is worse than showing slightly stale rows.
        try:
            prev = json.loads(data_path.read_text(encoding="utf-8"))
        except Exception:
            prev = {"rows": []}
        have = {r["retailer"] for r in fresh["rows"]}
        carried = []
        for r in prev.get("rows", []):
            if r.get("retailer") in have or r.get("status") == "pending":
                continue
            r = dict(r)
            r["note"] = ((r.get("note") or "") +
                         f" [carried forward from {r.get('checked','earlier')}; "
                         "source did not answer this run]").strip()
            carried.append(r)
        if carried:
            fresh["rows"].extend(carried)
            print(f"[WARN] carried forward {len(carried)} rows from {sorted({r['retailer'] for r in carried})}")

        data_path.write_text(json.dumps(fresh, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"Wrote {site_dir / 'data.json'}")
    except Exception as e:
        print(f"[FAIL] site data: {e}")
    out = Path(__file__).resolve().parent.parent / "README.md"
    out.write_text(readme, encoding="utf-8")
    print(f"\nWrote {out}")

if __name__ == "__main__":
    main()
