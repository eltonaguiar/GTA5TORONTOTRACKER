import json, sys, traceback
out = {}
# 1) curl_cffi TLS impersonation vs plain requests
try:
    from curl_cffi import requests as creq
    r = creq.get("https://tls.browserleaks.com/json", impersonate="chrome", timeout=25)
    j = r.json() if r.headers.get("content-type","").startswith("application/json") else {}
    out["curl_cffi_chrome"] = {"status": r.status_code, "ja3_hash": j.get("ja3_hash"), "ja4": j.get("ja4"), "user_agent": (j.get("user_agent") or "")[:80]}
except Exception as e:
    out["curl_cffi_chrome"] = {"error": f"{type(e).__name__}: {e}"}
try:
    import requests as preq
    r2 = preq.get("https://tls.browserleaks.com/json", timeout=25)
    j2 = r2.json()
    out["plain_requests"] = {"status": r2.status_code, "ja3_hash": j2.get("ja3_hash"), "ja4": j2.get("ja4")}
except Exception as e:
    out["plain_requests"] = {"error": f"{type(e).__name__}: {e}"}
# 2) Scrapling adaptive/local parse
try:
    from scrapling.parser import Adaptor
    html = '<html><body><div class="x9f2"><h2>Xbox Series X</h2><span class="a73k">In Stock</span></div></body></html>'
    page = Adaptor(html)
    txt = page.get_all_text()
    out["scrapling"] = {"ok": True, "text_sample": txt[:120], "has_stock_word": "In Stock" in txt}
except Exception as e:
    out["scrapling"] = {"ok": False, "error": f"{type(e).__name__}: {e}"}
# 3) nodriver / patchright versions + chrome presence
import shutil
out["chrome"] = {b: shutil.which(b) for b in ("google-chrome","chromium","chromium-browser")}
try:
    import nodriver, importlib.metadata as md
    out["nodriver"] = {"ok": True, "version": md.version("nodriver")}
except Exception as e:
    out["nodriver"] = {"ok": False, "error": str(e)}
try:
    import patchright, importlib.metadata as md
    out["patchright"] = {"ok": True, "version": md.version("patchright")}
except Exception as e:
    out["patchright"] = {"ok": False, "error": str(e)}
print(json.dumps(out, indent=2))
