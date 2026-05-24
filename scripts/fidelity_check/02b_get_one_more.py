"""Grab N more real phishing screenshots from live PhreshPhish URLs."""
import asyncio, json
from pathlib import Path
import requests
from datasets import load_dataset
from playwright.async_api import async_playwright

OUT = Path("scripts/fidelity_check/screenshots/real")
OUT.mkdir(parents=True, exist_ok=True)

NEED = 6  # how many to fetch

BRANDS = {
    "amazon","netflix","paypal","chase","linkedin","microsoft","apple",
    "instagram","facebook","dhl","zoom","airbnb","coinbase","wellsfargo",
    "citibank","usps","fedex","irs","bank","crypto","trezor","metamask",
}

LEGIT_DOMAINS = {
    "google.com","docs.google.com","youtube.com","twitter.com","github.com",
    "wikipedia.org","microsoft.com","apple.com","amazon.com","facebook.com",
    "instagram.com","linkedin.com","cnbc.com","bbc.com","reddit.com",
    "stackoverflow.com","turing.com","artnews.com","expertia.ai",
    "learn.microsoft.com","webindex.org","eldiario24.com","beehiiv.com",
    "investimonials.com","hrdive.com","fortune.com",
}

def is_live(url):
    try:
        r = requests.get(url, timeout=5, allow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        return r.status_code == 200 and len(r.content) > 1000
    except:
        return False

async def snap(url, out_path):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 800})
        try:
            await page.goto(url, wait_until="networkidle", timeout=15000)
            await asyncio.sleep(1)
            await page.screenshot(path=str(out_path))
        finally:
            await browser.close()
    return out_path.exists() and out_path.stat().st_size > 30000

# Load tried-URLs cache
TRIED_CACHE = OUT.parent / "tried_urls.json"
tried = set()
if TRIED_CACHE.exists():
    tried = set(json.loads(TRIED_CACHE.read_text()))

existing = len(list(OUT.glob("*.png")))
print(f"Have {existing} screenshots. Fetching {NEED} more...")
print("Streaming PhreshPhish...")

ds = load_dataset("phreshphish/phreshphish", split="train",
                  streaming=True, trust_remote_code=True)

from urllib.parse import urlparse

found = 0
checked = 0
for row in ds:
    if found >= NEED:
        break
    if row.get("label") != "phish" or row.get("lang") not in ("en", None, ""):
        continue
    target = (row.get("target") or "").lower()
    url = row.get("url", "")
    if not any(b in target or b in url.lower() for b in BRANDS):
        continue
    if url in tried:
        continue
    # Skip legit domains
    host = urlparse(url).netloc.lstrip("www.")
    if any(host == d or host.endswith("." + d) for d in LEGIT_DOMAINS):
        tried.add(url)
        continue
    tried.add(url)
    checked += 1
    if checked % 30 == 0:
        print(f"  tested {checked}, found {found}...")
    if not is_live(url):
        continue
    print(f"  LIVE: {url[:70]}")
    sha = row["sha256"][:12]
    brand = target[:10].replace("/","_") if target else "other"
    out = OUT / f"{brand}_{sha}.png"
    ok = asyncio.run(snap(url, out))
    if ok:
        print(f"  [ok] {out.name}  ({out.stat().st_size//1024}KB)")
        found += 1
    else:
        out.unlink(missing_ok=True)
        print(f"  [skip] too small")

TRIED_CACHE.write_text(json.dumps(list(tried)))
print(f"\nDone. Got {found}/{NEED}. Tested {checked} URLs.")
