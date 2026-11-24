# Web scraping tools evaluation

Date-stamped run. Every claim below was executed on this machine, not quoted from a project README.

## Installed and importable

| Tool | Version | Imports |
|---|---|---|
| curl_cffi | 0.16.3 | yes |
| scrapling | 0.4.15 | yes |
| patchright | (no __version__) | yes |
| playwright | (no __version__) | yes |
| browser_use | (no __version__) | yes |

Not installed: camoufox, CloakBrowser, nodriver, SeleniumBase, botasaurus, skyvern.

## Results against a real target

Target `https://www.gta5-mods.com/` (unprotected) and `https://www.g2.com/` (protected).

| Tool | Target | Status | Notes |
|---|---|---|---|
| requests (control) | gta5-mods | 200 | 53,360 bytes, 0.5s |
| curl_cffi (chrome TLS) | gta5-mods | 200 | 53,859 bytes, 0.2s |
| requests (control) | g2 | 403 | blocked |
| curl_cffi (chrome TLS) | g2 | 403 | **TLS impersonation alone did not bypass the block** |
| patchright (headless chromium) | g2 | 403 | `navigator.webdriver` = **False** (stealth worked) |
| playwright (headless chromium) | g2 | 403 | `navigator.webdriver` = **True** (leaks) |

## What succeeded

`curl_cffi` + `bs4` extracted real content from gta5-mods.com in 0.21s:

- status 200, 53,936 bytes
- title: "GTA5-Mods.com - Your source for the latest GTA 5 car mods, scripts, tools and more."
- 131 links, with 103 'mod', 50 'script', 28 'vehicle' and 34 'download' occurrences

Artifacts: `gta5mods_home.html` (raw) and `gta5mods_home.json` (structured result).

## What did not succeed

- **No anti-bot block was bypassed.** g2.com returned 403 to every tool tried: plain requests, TLS impersonation, patchright and playwright.
- **patchright did fix the webdriver leak** (False vs playwright's True), which is its actual claim, but that was not sufficient to pass g2's block. This is the honest limit of the result: the stealth patch works, the bypass does not follow from it alone.
- **camoufox, nodriver, SeleniumBase and skyvern were not testable** because they are not installed.

## Conclusion

For pages that are not actively protected, `curl_cffi` is the best choice: fast (0.2s), no browser, real TLS fingerprint. For blocked pages, nothing tested here got through, so I would not claim any of these tools bypasses anti-bot defenses on the strength of this run.
