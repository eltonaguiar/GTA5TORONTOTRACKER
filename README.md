# GTA5 Toronto Console Tracker

Tracking availability of PS5 and Xbox Series X|S in Downtown Toronto and the GTA.

## Current Stock Status (as of 2026-11-20)

### ⚠️ ALL DIGITAL SOURCES CURRENTLY UNSTABLE
Recent audits show widespread DNS and SSL failures across major retail links (including GameStop). **Do not rely on web links for immediate stock verification.**

### 📞 MANDATORY PHONE VERIFICATION
Since digital portals are failing (DNS_PROBE_FINISHED_NXDOMAIN / SSL Mismatch), you must call stores directly to verify actual shelf stock.

- **GameStop (Downtown Locations)**
  - Method: Call the specific branch nearest to you.
- **Gamerama**
  - Address: 2470 Yonge Street, Toronto, ON M4P 2H5
  - Phone: 416-487-8802
- **Queen East Appliance Centre**
  - Address: 1180 Queen St E, Toronto, ON M4M 1L4
  - Phone: +1 416-463-6551
- **ReserveRoom.ca**
  - Phone: +1 (647) 809-5721
- **Buy & Sell Kings**
  - Address: 2852 Danforth Ave, Toronto, ON M4C 1M1
  - Phone: 647-348-1763

## Search Area
- Primary: Downtown Toronto
- Secondary: Greater Toronto Area (GTA)

## Verified Digital Check — 2026-11-20T20:53Z (Playwright 1.58.2, Chromium headless)

Measured by rendering each site in a real browser, not by trusting HTTP status codes.
**This corrects the "ALL DIGITAL SOURCES CURRENTLY UNSTABLE" note above**: the failures
are not uniform DNS/SSL failures. One major downtown-capable retailer is fully readable.

### Reachable and checked

- **Canada Computers** — loads normally (HTTP 200).
  - Xbox Series X 1TB Black — **SOLD OUT online and at all locations**
    https://www.canadacomputers.com/en/xbox/184244/microsoft-xbox-series-x-1tb-black-rrt-00001.html
  - Xbox Series X 1TB Digital, Robot White — **SOLD OUT online and at all locations**
    https://www.canadacomputers.com/en/xbox/264257/xbox-series-x-1tb-digital-console-robot-white-ep2-00692.html
  - PlayStation 5 — search returned no console listing that could be verified. **Not confirmed either way.**

### Blocked — could not be verified digitally

| Retailer | Result | Why |
|---|---|---|
| Best Buy Canada | HTTP 403 "Access Denied" | Bot protection, **not** DNS or SSL |
| GameStop / EB Games CA | connection failed | unreachable from the checking host |
| Walmart Canada | 301 redirect | not readable |

### Needs a human check

- Best Buy CA — https://www.bestbuy.ca/en-ca/search?search=playstation+5+console
- Walmart CA — https://www.walmart.ca/
- GameStop CA — https://www.gamestop.ca/
- Canada Computers store pickup — https://www.canadacomputers.com/en/ (per-store availability is behind their pickup selector)

### Internet cafes

Not verifiable digitally — small businesses with no machine-readable inventory.
A phone call is the only reliable method. **No claim is made about their stock.**

### Method note

Counts of "Add to cart" vs "Sold Out" on a search page are **not** store-level stock and
were deliberately not used as evidence. Only per-product pages stating availability were
treated as findings. Nothing verified above was in stock in Downtown Toronto at check time,
so the GTA search area remains the fallback.
