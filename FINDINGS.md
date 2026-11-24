# Scrape findings — subq

Kept outside README.md because `stock-monitor.yml` regenerates README and has already
wiped hand-written sections once. Numbers that belong in the tables are in README;
reasoning and caveats live here.

## Scrape findings — authenticated session, 2026-11-20T21:36Z

Method note worth keeping: a fresh headed Chromium on the virtual display crashed
(`EGL display types failed`), so these were read by **attaching over CDP** to an
already-running, logged-in Chrome. Reusing a live browser avoided the GPU init
entirely. Every page below returned HTTP 200 and was **not** bot-blocked.

| Target | Status | What the page showed | Reading |
|---|---|---|---|
| Best Buy — PS5 Slim Disc | 200, not blocked | "add to cart" **and** "sold out"/"out of stock"; $1,299.99, $1,199.99, accessory $109.99 | **Ambiguous.** Mixed signals on one page — do not conclude the console is in stock. The availability API said `InStockOnlineOnly qty=1` at $1,699.99 from a marketplace seller, while the page's first-party price reads $1,299.99. Two different offers. |
| Best Buy — Xbox Series S 512GB | 200, not blocked | $649.99 (compare $749.99), "add to cart", accessory $79.99 | **Corroborated.** Matches the availability API independently: `InStock qty=587 purchasable=True`. Two channels agree. |
| Google Shopping — "new ps5" | 200, not blocked | Prices $749.99 → $4,998.48 | Floor $749.99 is plausible for a PS5; multi-thousand entries are bundles/marketplace/PCs miscategorised. Trust the floor, ignore outliers. |

### Lesson

Keyword scraping is not a stock check. The PS5 page contained "add to cart" and
"sold out" simultaneously — a regex would have called it available. Per-SKU
availability JSON (`InStock` / `SoldOutOnline` / `InStockOnlineOnly`) is the
only signal that distinguishes "the console" from "a controller on the same page".

## Xbox scrape — 2026-11-20T21:37Z

Same authenticated CDP session. Where a page was ambiguous, the per-SKU
availability API was queried instead of trusting keywords.

| Source | Result | Reading |
|---|---|---|
| Best Buy API — Series S 512GB (19422130) | `InStock qty=577` | ✅ Buyable, delivery only. qty fell 587 → 577 in ~26 min, so it is real moving inventory, not a static flag. |
| Best Buy API — Series S 1TB (19422127) | `SoldOutOnline qty=0` | ⛔ |
| Best Buy API — Series X 1TB (20189840) | `SoldOutOnline qty=0` | ⛔ |
| Best Buy API — Series X 1TB Digital (19422129) | `SoldOutOnline qty=0` | ⛔ |
| Best Buy Xbox landing page | 200, prices $649.99 … $1,149.99, "in stock" | Browse page — mixed SKUs, not attributable to one console |
| Microsoft Store Xbox | 200, "in stock" | Generic boilerplate text; no per-console status extracted |
| Google Shopping — "xbox series x" | $769.99 … $2,999.00 | Wide spread = bundles/marketplace; no stock word at all |
| Canada Computers — Series X 1TB | 200, $729.99, **"sold out"** | ⛔ sold out online + all locations |

### Reading

- **Series S 512GB at Best Buy is the one genuinely buyable Xbox**, and the only
  console in this tracker with live, corroborated inventory — API says InStock,
  the rendered page showed "Add to Cart", and the quantity is decreasing.
- **Every Series X SKU is sold out** at Best Buy, and the Series X is sold out at
  Canada Computers too. If you want a Series X specifically, there is no verified
  stock right now.
- A page saying "in stock" is worthless without a SKU: the Best Buy Xbox landing
  page mixes a $649.99 console with $1,149.99 bundles.

---

## chrome-devtools-mcp — evaluated 2026-11-24

**What it is.** `chrome-devtools-mcp` v1.13.0, the Chrome DevTools team's official
MCP server (npm, ~29 tools). Under the hood it is **Puppeteer driving the Chrome
DevTools Protocol** — the same transport this tracker already uses.

**Tested, not assumed:**

| Check | Result |
|---|---|
| `npm view chrome-devtools-mcp version` | `1.13.0` |
| `npx -y chrome-devtools-mcp@latest --help` | runs; flags confirmed |
| Connection modes | `--browserUrl http://127.0.0.1:9222`, `--wsEndpoint`, `--autoConnect` |
| Profile isolation | `--isolated` (temp dir, auto-cleaned), `--userDataDir`, `--channel`, `--executablePath` |
| Tool trimming | `--categoryInput/Navigation/Emulation/Network/...` booleans |
| Other | `--headless`, `--proxyServer`, `--chromeArg` |

**Verdict — it is a transport, not a bypass.** It launches or attaches to a *real*
Chrome, which is exactly what a Playwright/CDP scrape already does. Best Buy returned
`🐴 Access Denied` (Akamai) through a real Chrome today, so no MCP layer changes that.

What it genuinely adds, and why it is still worth having:

1. **A standard tool surface** — navigate, click, type, read DOM, read network, run a
   performance trace — so an agent scrapes without hand-writing CDP plumbing per site.
2. **Network interception and mocking**, which is how you read a retailer's own
   availability XHR instead of parsing rendered HTML (the fragile part).
3. **`--isolated`** profiles, so scraping never touches the user's logged-in Chrome.
4. **`--category*` flags** to cut the tool list down to navigation + network only.

Where it does **not** help: Akamai/Cloudflare walls, IP reputation, or JS challenges.
For those the honest answer stays the same — use the retailer's own JSON/HTML where it
is open, and mark the rest manual.

## Fresh check — 2026-11-24 03:53–03:59 EST

| Source | Method | Result |
|---|---|---|
| Canada Computers, 7 console SKUs | static HTML, per-store table, **40 stores parsed per SKU** | **All zero.** Toronto Downtown (312 Yonge) qty=0 and every other store qty=0 for Series X 1TB, Series X 1TB Digital RW, Series S 512GB, Series S 1TB, PS5 Slim Disc, PS5 Slim Digital 825GB, PS5 Pro |
| Best Buy API @ M5G 1L7 | `ecomm-api/availability` | **Series S 512GB `InStock qty=105`.** Every other console `SoldOutOnline qty=0` (Series X 1TB Digital RW, PS5 Slim Digital, PS5 Slim 1TB, PS5 Pro, PS5 Slim 1TB Refurb) |
| Best Buy product page | real browser | `🐴 Access Denied` — Akamai. API is a lead here, not proof |
| Amazon.ca Series S 512GB (B0FLL9VRL5) | real browser | ✅ **"In Stock"**, add-to-cart present, $649.96, FREE delivery Nov 28 / fastest **Nov 25** |
| Amazon.ca Series X 1TB (B0BMXVWSD6) | real browser | ⚠️ "Only 2 left in stock" at **$1,299.50 sold by `CCJamesInc`** — third-party marketplace markup, no visible add-to-cart. **Not a retail find.** |
| Amazon.ca PS5 Disc (B0BCSYVXGL) | real browser | ⚠️ "Only 1 left in stock", no price, no add-to-cart — unconfirmed |
| Amazon.ca PS5 B0FRGMYJMG / B0CL7RQRY9 / B0CL7NKBBL | real browser | ⛔ Dead listings: $129.98 / $229.99 (not console prices), availability block empty |

### Lesson

Two failure modes to keep watching for:

1. **ASIN and SKU drift.** A console's old ASIN becomes a dead listing that still
   renders a title and a nonsense price (`$129.98` for a PS5). Price sanity-check
   against MSRP is what catches it.
2. **A low price with no availability block and no add-to-cart is a dead page**, not
   a bargain — and a high price with "only N left" is usually a marketplace reseller.
   `soldBy` is the tie-breaker: `CCJamesInc` at $1,299.50 is not a retail restock.

### The one live signal

Best Buy's Series S 512GB quantity is the only corroborated inventory in this tracker,
and it is draining: **587 → 577** (2026-11-20) → **105** (2026-11-24). Amazon
independently shows the same console in stock with next-day delivery, which is the
first two-source agreement on a buyable console since this tracker started.

## 2026-11-24 — two corrections: games listed as consoles; Staples status was wrong

### 1. Games were listed as consoles
The Staples query returned game SKUs and the table listed them as hardware, e.g.
"Microsoft Forza Motorsport for XBox Series X [Disc]" ($89.99). That is not a console.

**Fix:** `scripts/check_stock.py` now has `is_console(name)` — the name must match
`xbox series X/S` or `PlayStation 5`/`PS5` **and** must not match a game/accessory/
bundle list (`forza|nba|nhl|fifa|madden|spider-man|game|jeu|controller|manette|
headset|casque|charging|dock|accessor|bundle|lot|skin|case|steelbook`). The filter is
applied at fetch time and again at render time.

### 2. Staples "available online" was false
Shopify `search/suggest.json` reported `available: true` for every SKU, but the
product page's JSON-LD said otherwise. Checked all 10 Staples SKUs from the table:

| Handle (prefix) | JSON-LD availability |
|---|---|
| 3103551 (PS5 Pro, EN + FR) | **OutOfStock** |
| 3140351 (PS5 Digital/Slim 825GB, EN + FR) | **OutOfStock** |
| 3140352 (PS5 Slim 1TB/1To, EN + FR) | **OutOfStock** |
| 3104045 (Xbox Series X Digital 1TB, EN + FR) | **OutOfStock** |
| 2993232 (Xbox Series X, EN + FR) | **OutOfStock** |

**Fix:** `fetch_staples()` no longer trusts `suggest.json.available`. It fetches each
product page and reads `"availability": "https://schema.org/OutOfStock|InStock"`
(from JSON-LD), with an "out of stock / sold out" text fallback. If the page cannot
be read, the row says **check failed** — never a fake "available".

### Guard
`scripts/assert_console_only.py` fails if any row in README's console tables contains
a game/accessory/bundle. It runs in `.github/workflows/stock-monitor.yml` immediately
after the scrape step, so a regression cannot be auto-committed.

**Verified after fix:** `grep -ciE "forza|nba|nhl|fifa|madden" README.md` → **0**;
guard → **OK**; 6 console rows kept from Staples, all ❌ OutOfStock.

## 2026-11-24 — Walmart discovery (category + search + product URLs)
`fetch_walmart()` now discovers consoles from Walmart's Next.js payloads:
- PS5 category `browse/video-games/playstation-5/10012_6000201024440`
- searches `xbox series x console` and `xbox series s console`
- two first-party Series S product URLs (user-supplied)

It reads `availabilityStatusV2.value == IN_STOCK`, `isOutOfStock == false` and
`canAddToCart == true`, and only lists in-stock consoles. Bundles with games
(Fortnite/Minecraft/Halo), accessories (controller-only, headset, disc drive,
wall mount, racing wheel), and marketplace duplicates are excluded; marketplace
sellers are labelled and sorted after first-party.

**Challenge behaviour:** our IP was served "Verify Your Identity" for the
category page and the two product URLs, while the search pages still returned
parsed items. On a challenge the row set is empty and printed as `[CHALLENGE]`
— the tracker never guesses stock. The parser was verified earlier on a real
54-item payload; GitHub Actions runs from a different IP.
