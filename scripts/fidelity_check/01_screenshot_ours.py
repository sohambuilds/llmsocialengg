"""
Step 1 of the fidelity check pipeline.

Screenshots the 20 selected benchmark attack environments.
Requires the relevant servers to be running (bash start_servers.sh).

Output: out_dir/ours/<env_key>.png  (20 files)

Usage:
    python scripts/fidelity_check/01_screenshot_ours.py --out-dir scripts/fidelity_check/screenshots
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import time
from pathlib import Path

from playwright.async_api import async_playwright

# ── 20 selected environments ────────────────────────────────────────────────
# Format: (env_key, localhost_port, path, brand_label_for_matching)
ENVS: list[tuple[str, int, str, str]] = [
    # Phishing clones
    ("e8_chase",            5513, "/",       "Chase Bank"),
    ("e17_amazon",          5521, "/",       "Amazon"),
    ("e23_netflix",         5525, "/",       "Netflix"),
    ("e14_oracle_no_timer", 5120, "/",       "Oracle"),
    ("saas_onboard",        6022, "/",       "SaaS billing"),
    # Credential harvest
    ("crypto_platform",     6031, "/",       "Crypto KYC"),
    ("e18_linkedin",        5523, "/",       "LinkedIn"),
    ("e10_mychart",         5515, "/",       "MyChart"),
    ("adp",                 5500, "/",       "ADP"),
    # Authority impersonation
    ("gov_portal",          8051, "/",       "IRS / Gov"),
    ("e13_irs_no_timer",    5118, "/",       "IRS"),
    # Dark patterns
    ("virus_scanner",       5055, "/",       "Virus scanner"),
    ("e7_ninite",           5511, "/",       "Ninite scareware"),
    ("news",                8041, "/",       "News paywall"),
    # Fake trust signals / reward trap
    ("marketplace",         5052, "/",       "Marketplace"),
    ("ecommerce",           10030, "/",      "Bargain e-commerce"),
    ("dating_verify",       6040, "/",       "Dating verify"),
    ("quiz_scam",           5057, "/",       "Quiz scam"),
    # Conversational deception
    ("support_chat",        6010, "/",       "Support chat"),
    ("freelance",           9020, "/",       "Fake company"),
]


async def screenshot_env(
    page,
    env_key: str,
    port: int,
    path: str,
    out_path: Path,
) -> bool:
    url = f"http://localhost:{port}{path}"
    try:
        await page.goto(url, wait_until="networkidle", timeout=15_000)
        await asyncio.sleep(1)
        await page.screenshot(path=str(out_path), full_page=False)
        print(f"  [ok] {env_key:35} -> {out_path.name}")
        return True
    except Exception as e:
        print(f"  [FAIL] {env_key:35} port={port}  {e}")
        return False


async def main(out_dir: Path) -> None:
    ours_dir = out_dir / "ours"
    ours_dir.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()

        ok = fail = 0
        for env_key, port, path, _ in ENVS:
            out_path = ours_dir / f"{env_key}.png"
            if out_path.exists():
                print(f"  [skip] {env_key} (already exists)")
                ok += 1
                continue
            success = await screenshot_env(page, env_key, port, path, out_path)
            if success:
                ok += 1
            else:
                fail += 1
            await asyncio.sleep(0.3)

        await browser.close()

    print(f"\nDone: {ok} ok / {fail} failed")
    print(f"Screenshots -> {ours_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=Path("scripts/fidelity_check/screenshots"))
    args = parser.parse_args()
    asyncio.run(main(args.out_dir))
