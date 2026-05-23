"""
Step 2 of the fidelity check pipeline.

Finds real phishing pages by streaming PhreshPhish, testing if each URL is
still live, and screenshotting the ones that respond.

No Wayback, no urlscan — just hitting the actual phishing URLs directly.
Roughly 5-15% of PhreshPhish URLs are still live (bulletproof hosts).

Output: out_dir/real/<brand>_<hash>.png
Usage:
    python scripts/fidelity_check/02_screenshot_real.py --out-dir scripts/fidelity_check/screenshots --n 20
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
from pathlib import Path

import requests
from playwright.async_api import async_playwright

MIN_PNG_BYTES = 30_000  # 30 KB — rejects blank/error pages

TARGET_BRANDS = {
    "amazon", "netflix", "paypal", "chase", "linkedin", "microsoft",
    "apple", "google", "irs", "airbnb", "zoom", "instagram", "facebook",
    "dhl", "oracle", "adp", "docusign", "dropbox", "wellsfargo", "citibank",
    "fedex", "ups", "usps", "bank", "crypto", "coinbase", "metamask",
}

def is_live(url: str, timeout: int = 6) -> bool:
    """Return True if the URL responds with HTTP 200."""
    try:
        r = requests.get(url, timeout=timeout, allow_redirects=True,
                         headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
        return r.status_code == 200 and len(r.content) > 500
    except Exception:
        return False


async def screenshot_url(page, url: str, out_path: Path) -> bool:
    try:
        await page.goto(url, wait_until="networkidle", timeout=18_000)
        await asyncio.sleep(1)
        await page.screenshot(path=str(out_path), full_page=False)
        size = out_path.stat().st_size
        if size < MIN_PNG_BYTES:
            out_path.unlink(missing_ok=True)
            return False
        return True
    except Exception:
        out_path.unlink(missing_ok=True)
        return False


async def main(out_dir: Path, n: int, scan_limit: int) -> None:
    real_dir = out_dir / "real"
    real_dir.mkdir(parents=True, exist_ok=True)

    existing = list(real_dir.glob("*.png"))
    need = n - len(existing)
    if need <= 0:
        print(f"[real] Already have {len(existing)}/{n}. Nothing to do.")
        return
    print(f"[real] Need {need} more (have {len(existing)}/{n}). Scanning up to {scan_limit} PhreshPhish rows...")

    try:
        from datasets import load_dataset
    except ImportError:
        raise SystemExit("pip install datasets")

    ds = load_dataset("phreshphish/phreshphish", split="train", streaming=True, trust_remote_code=True)

    # Collect candidates
    candidates = []
    checked = 0
    for row in ds:
        checked += 1
        if checked % 2000 == 0:
            print(f"  scanned {checked} rows, {len(candidates)} candidates...")
        if row.get("label") != "phish":
            continue
        if row.get("lang") not in ("en", None, ""):
            continue
        target = (row.get("target") or "").lower()
        url = row.get("url", "")
        if not any(b in target or b in url.lower() for b in TARGET_BRANDS):
            continue
        candidates.append({"url": url, "target": target, "sha": row["sha256"][:12]})
        if len(candidates) >= scan_limit:
            break

    print(f"[real] {len(candidates)} brand-matched phishing candidates from {checked} rows.")
    print(f"[real] Testing which are still live (this takes a while)...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()

        saved = 0
        tested = 0
        for cand in candidates:
            if saved >= need:
                break
            tested += 1
            url = cand["url"]
            brand = (cand["target"] or "unknown")[:12].replace("/", "_")
            sha = cand["sha"]
            out_path = real_dir / f"{brand}_{sha}.png"
            if out_path.exists():
                saved += 1
                continue

            # Quick liveness check first (fast, no browser)
            if not is_live(url):
                continue

            print(f"  [live!] {url[:70]}")
            ok = await screenshot_url(page, url, out_path)
            if ok:
                size_kb = out_path.stat().st_size // 1024
                print(f"  [ok]   {brand:14} {size_kb:4d}KB -> {out_path.name}")
                saved += 1
            else:
                print(f"  [skip] screenshot too small or failed")

        await browser.close()

    final = list(real_dir.glob("*.png"))
    print(f"\nDone: {len(final)}/{n} real screenshots -> {real_dir}")
    if len(final) < n:
        print(f"  Only {len(final)} live phishing pages found in {tested} tested.")
        print(f"  Try --scan-limit {scan_limit * 2} to scan more rows.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=Path("scripts/fidelity_check/screenshots"))
    parser.add_argument("--n", type=int, default=20)
    parser.add_argument("--scan-limit", type=int, default=3000,
                        help="Max PhreshPhish rows to scan (default 3000)")
    args = parser.parse_args()
    asyncio.run(main(args.out_dir, args.n, args.scan_limit))
