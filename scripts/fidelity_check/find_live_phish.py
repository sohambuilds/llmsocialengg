"""Stream PhreshPhish and print live phishing URLs. No screenshots."""
import json
from pathlib import Path
from urllib.parse import urlparse
import requests
from datasets import load_dataset

NEED = 20

BRANDS = {
    "amazon","netflix","paypal","chase","linkedin","microsoft","apple",
    "instagram","facebook","dhl","zoom","airbnb","coinbase","wellsfargo",
    "citibank","usps","fedex","irs","bank","crypto","trezor","metamask",
    "dropbox","docusign","att","verizon","steam","ebay","twitter","snapchat",
}

LEGIT_DOMAINS = {
    "google.com","docs.google.com","youtube.com","twitter.com","github.com",
    "wikipedia.org","microsoft.com","apple.com","amazon.com","facebook.com",
    "instagram.com","linkedin.com","cnbc.com","bbc.com","reddit.com","zoom.us",
    "webindex.org","turing.com","artnews.com","expertia.ai","learn.microsoft.com",
    "eldiario24.com","beehiiv.com","investimonials.com","hrdive.com","fortune.com",
    "adobe.com","express.adobe.com","new.express.adobe.com","privacybee.com",
}

TRIED_CACHE = Path("scripts/fidelity_check/screenshots/tried_urls.json")
tried = set()
if TRIED_CACHE.exists():
    tried = set(json.loads(TRIED_CACHE.read_text()))

def is_live(url):
    try:
        r = requests.get(url, timeout=5, allow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        return r.status_code == 200 and len(r.content) > 2000
    except:
        return False

print("Streaming PhreshPhish train split...")
ds = load_dataset("phreshphish/phreshphish", split="train",
                  streaming=True, trust_remote_code=True)

found = []
checked = 0

for row in ds:
    if len(found) >= NEED:
        break
    if row.get("label") != "phish" or row.get("lang") not in ("en", None, ""):
        continue
    target = (row.get("target") or "").lower()
    url = row.get("url", "")
    if not any(b in target or b in url.lower() for b in BRANDS):
        continue
    if url in tried:
        continue
    host = urlparse(url).netloc.lstrip("www.")
    if any(host == d or host.endswith("." + d) for d in LEGIT_DOMAINS):
        tried.add(url)
        continue
    tried.add(url)
    checked += 1
    if checked % 20 == 0:
        print(f"  checked {checked}, found {len(found)}...")
    if not is_live(url):
        continue
    found.append({"target": target, "url": url})
    print(f"  [{len(found):02d}] {target:15} {url}")

print(f"\n--- {len(found)} live phishing URLs ---")
for i, r in enumerate(found, 1):
    print(f"{i:02d}. [{r['target']:15}] {r['url']}")

TRIED_CACHE.write_text(json.dumps(list(tried)))
