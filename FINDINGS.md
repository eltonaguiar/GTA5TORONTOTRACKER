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
