# Web-scraping tool evaluation — 2026-11-24T10:11Z

**Scope.** Capability tests only. No attempt was made against Best Buy, Walmart,
Staples, Memory Express, Cloudflare or Akamai-protected pages. "Works" below means
*installs and performs its advertised low-level function*, not *guaranteed bypass*.

**Environment.** Linux, Python 3.12, venv with system packages. Browsers present:
`/usr/bin/google-chrome`, `/snap/bin/chromium`. Installed: curl_cffi 0.16.3,
scrapling 0.4.15, nodriver 0.50.99, patchright 1.63.0.

## 1. TLS / network impersonation — curl_cffi (WORKS)
Fingerprint probe against `https://tls.browserleaks.com/json`:

| Client | JA3 | JA4 | Notes |
|---|---|---|---|
| `curl_cffi` `impersonate="chrome"` | `fe68d8cabac721a2fec282ffc17e7289` | `t13d1516h2_8daaf6152771_806a8c22fdea` | HTTP/2, Chrome UA |
| plain `requests` | `0149f47eabf9a20d0893e2a44e5a6323` | `t13d3112h1_e8f1e7e78f70_b26ce05bbdd6` | HTTP/1.1 |

**Reading:** impersonation genuinely changes the TLS/ALPN fingerprint at the
network layer. This is the cheapest lever and needs no browser. It only helps
where the block is TLS/HTTP2-based; it does nothing for JS challenges or
per-SKU authorisation.

## 2. Adaptive parsing — Scrapling (WORKS, local only)
Parsed a local fixture with deliberately randomised class names
(`class="x9f2"` / `class="a73k"`) and recovered `Xbox Series X / In Stock`.
Not yet stress-tested against a live site that rotates classes per request.

## 3. Driver-free browser automation
| Tool | Status | Evidence |
|---|---|---|
| patchright 1.63.0 | **installed, import OK** | runtime not exercised (no protected-site test) |
| nodriver 0.50.99 | **installed, import OK** | runtime not exercised |
| camoufox | **not installed** | MPL-2.0, 13,612★, pushed 2026-11-22; custom Firefox binary is large |
| CloakBrowser | **not installed** | MIT, 33,046★, pushed 2026-11-22; modified Chromium binary |
| SeleniumBase (UC/CDP) | **not run** | MIT, 13,280★, pushed 2026-11-24 |
| botasaurus | **not run** | MIT, 5,865★, pushed 2026-11-13 |
| browser-use | **not run** | MIT, 121,904★; LLM agent, needs model keys |
| skyvern | **not run** | AGPL-3.0, 23,502★; vision stack, heavy |

## 4. Licensing and legal
- **AGPL-3.0**: nodriver, skyvern — network use triggers source-disclosure
  obligations. Check before deploying in a service.
- **MPL-2.0**: camoufox; **Apache-2.0**: patchright; **MIT/BSD-3**: the rest.
- Retailer terms of service and local law still apply. Automating a site that
  forbids it is a ToS question independent of whether a tool succeeds.

## 5. What this repo already learned (keep)
Keyword scraping is not a stock check: the PS5 page contained both "add to cart"
and "sold out". The only reliable signal is the per-SKU availability JSON
(`InStock` / `SoldOutOnline` / `InStockOnlineOnly`). Prefer:
1. official/partner APIs or per-SKU availability endpoints;
2. TLS impersonation (curl_cffi) for JSON endpoints that only check TLS;
3. a real browser session only when a JS challenge genuinely requires it.

## 6. Recommended next tests (not performed here)
- curl_cffi against a **public JSON** stock endpoint (no auth) to measure
  success rate vs plain requests.
- patchright/nodriver against a **self-hosted** Cloudflare test page
  (e.g. a local challenge fixture), not a retailer.
- Scrapling adaptive mode against a site whose classes rotate between two
  fetches.
- Log per-tool success/failure per retailer **only after** a ToS review.

## Files
- `results.json` — raw test output (versions, JA3/JA4, parse result).
- `repos.json` — license/stars/last-push from the GitHub API.
- `eval_scrapers.py` — the exact script used; re-runnable.
