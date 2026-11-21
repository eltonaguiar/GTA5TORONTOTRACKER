# GTA Toronto Console Tracker

In-stock check for **Xbox Series X / S** and **PlayStation 5** for **downtown Toronto / GTA** (delivery or pickup near M5G).

- **Verified** rows = read in a real browser (Amazon) or scraped from the product page's embedded stock table (Canada Computers).
- **Unverified** rows = retailer blocks automated browsers → a human must confirm (link/phone given).
- All times **EST**. This file is auto-updated by `.github/workflows/stock-monitor.yml`.

_Last auto-check (Canada Computers): **2026-11-21 13:06 EST**._

## Table 1 — VERIFIED

| Console | Price | Status | Where / delivery to downtown (M5G) | Link | Last updated (EST) |
|---|---|---|---|---|---|
| Xbox Series X 1TB | $1,299.50 | ✅ In Stock | Amazon.ca — FREE delivery Nov 26–27 | https://www.amazon.ca/dp/B0BMXVWSD6 | 2026-11-20 16:20 |
| Xbox Series S 512GB | $649.96 | ✅ In stock (Add to Cart) | Amazon.ca — delivery Sat Dec 5 | https://www.amazon.ca/dp/B0FLL9VRL5 | 2026-11-20 16:20 |
| PS5 Digital Edition (Slim) | $1,099.99 | ✅ "Only 4 left in stock" | Amazon.ca — delivery Nov 26–27 | https://www.amazon.ca/dp/B0CL7NKBBL | 2026-11-20 16:20 |
| Xbox Series X 1TB (Black) | — | ⛔ Sold out (online + all stores) | Canada Computers — sold out online + all locations | https://www.canadacomputers.com/en/xbox/184244/microsoft-xbox-series-x-1tb-black-rrt-00001.html | 2026-11-21 13:06 EST |
| Xbox Series X 1TB Digital (Robot White) | — | ⛔ Sold out (online + all stores) | Canada Computers — sold out online + all locations | https://www.canadacomputers.com/en/xbox/264257/xbox-series-x-1tb-digital-console-robot-white-ep2-00692.html | 2026-11-21 13:06 EST |
| Xbox Series S 512GB | — | ⛔ Sold out (online + all stores) | Canada Computers — sold out online + all locations | https://www.canadacomputers.com/en/xbox/184250/microsoft-xbox-series-s-512-gb-all-digital-console-white-rrs-00001.html | 2026-11-21 13:06 EST |
| Xbox Series S 1TB | — | ⛔ Sold out (online + all stores) | Canada Computers — sold out online + all locations | https://www.canadacomputers.com/en/xbox/264253/microsoft-xbox-series-s-1tb-console-robot-white-ep2-00634.html | 2026-11-21 13:06 EST |
| PS5 Slim (Disc) | — | ⛔ Sold out (online + all stores) | Canada Computers — sold out online + all locations | https://www.canadacomputers.com/en/playstation/247956/sony-playstation-5-slim-console-1000039655-1000049888.html | 2026-11-21 13:06 EST |
| PS5 Slim Digital 825GB | — | ⛔ Sold out (online + all stores) | Canada Computers — sold out online + all locations | https://www.canadacomputers.com/en/playstation/247955/sony-playstation-5-slim-console-digital-edition-1000039669-1000049898.html | 2026-11-21 13:06 EST |
| PS5 Pro | — | ⛔ Sold out (online + all stores) | Canada Computers — sold out online + all locations | https://www.canadacomputers.com/en/playstation/263621/sony-playstation-5-pro-digital-edition-1000046547-1000050805.html | 2026-11-21 13:06 EST |

**How to read it:** a Canada Computers row turns ✅ the moment the store page shows an online or in-store quantity > 0. Toronto Downtown = 312 Yonge St; GTA stores (Markham, etc.) count too.

## Table 2 — UNVERIFIED (site blocks bots — manual check required)

| Retailer / Store | What to check | Why unverified | Link / phone | Last checked (EST) |
|---|---|---|---|---|
| Best Buy Canada | Xbox Series S in stock online (API); Series X & PS5 sold out online | Akamai "Access Denied" to bots | https://www.bestbuy.ca/en-ca/product/xbox-series-s-512gb-console/19422130 | 2026-11-20 16:00 |
| Best Buy Canada | PS5 Slim / Series X | Akamai block | https://www.bestbuy.ca/en-ca/product/playstation-5-slim-1tb-console/19446111 | 2026-11-20 16:00 |
| EB Games / GameStop (267 Yonge St) | PS5 / Xbox store stock | Cloudflare; gamestop.ca does not resolve | https://www.ebgames.ca/ | 2026-11-20 16:00 |
| Walmart Canada | Consoles | "Forbidden" bot block | https://www.walmart.ca/en/search?q=playstation+5 | 2026-11-20 16:00 |
| Staples | Consoles | Cloudflare challenge | https://www.staples.ca/search?query=playstation+5 | 2026-11-20 16:00 |
| Memory Express | Consoles | Cloudflare challenge | https://www.memoryexpress.com/ | 2026-11-20 16:00 |
| Gamerama (local) | Xbox/PS5 shelf stock | Phone verify | 2470 Yonge St — 416-487-8802 | 2026-11-20 16:00 |
| Queen East Appliance Centre (local) | Consoles | Phone verify | 1180 Queen St E — 416-463-6551 | 2026-11-20 16:00 |
| ReserveRoom.ca (local) | PS5/Xbox stock | Phone verify | +1 647-809-5721 | 2026-11-20 16:00 |
| Buy & Sell Kings (local) | New/used consoles | Phone verify | 2852 Danforth Ave — 647-348-1763 | 2026-11-20 16:00 |

## Notes
- Canada Computers "Toronto Downtown" = 312 Yonge Street, Toronto, ON M5B 1R4.
- Auto-monitor covers Canada Computers (server-rendered stock table). Amazon rows are a manual browser snapshot. Bot-walled retailers need a human.
- Run locally: `python scripts/check_stock.py` (install `curl_cffi`). Cron example: `*/30 * * * * cd /path/repo && python scripts/check_stock.py && git commit -am auto && git push`.
