"""
Slide 7 generator: starts 4 env servers, screenshots them, composes slide PNG.
"""
import subprocess, sys, time, os, signal, textwrap
from pathlib import Path

ROOT = Path(__file__).parent
VENV_PYTHON = ROOT / ".venv/Scripts/python.exe"
if not VENV_PYTHON.exists():
    VENV_PYTHON = ROOT / ".venv/bin/python"
PYTHON = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable

SERVERS = [
    # (label, script_path, port, env_cwd)
    ("job_portal_phish",  ROOT / "all_websites/job-app-website/phishing_site/app.py", 12999, ROOT / "all_websites/job-app-website/phishing_site"),
    ("github_phish",      ROOT / "all_websites/subfolder/app.py", 5053, ROOT / "all_websites/subfolder"),
    ("github_phish_scar", ROOT / "all_websites/github_phish_scarcity/app.py", 5135, ROOT / "all_websites/github_phish_scarcity"),
    ("support_chat",      ROOT / "all_websites/support-chat/store/app.py", 6010, ROOT / "all_websites/support-chat/store"),
]

SCREENSHOTS = {
    "phishing_clone": ("http://localhost:12999/", ROOT / "slide7_phish.png"),
    "github_phish_parent": ("http://localhost:5053/", ROOT / "slide7_parent.png"),
    "github_phish_scarcity": ("http://localhost:5135/", ROOT / "slide7_scarcity.png"),
    "support_chat": ("http://localhost:6010/", ROOT / "slide7_chat.png"),
}

procs = []

def start_servers():
    for label, script, port, cwd in SERVERS:
        env = os.environ.copy()
        env["FLASK_ENV"] = "production"
        p = subprocess.Popen(
            [PYTHON, str(script)],
            cwd=str(cwd),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env,
        )
        procs.append(p)
        print(f"  Started {label} (pid {p.pid}) on port {port}")
    print("  Waiting 6s for servers to come up...")
    time.sleep(6)

def stop_servers():
    for p in procs:
        try:
            p.terminate()
        except Exception:
            pass
    time.sleep(1)
    for p in procs:
        try:
            p.kill()
        except Exception:
            pass

def take_screenshots():
    from playwright.sync_api import sync_playwright
    shots = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        for key, (url, out_path) in SCREENSHOTS.items():
            print(f"  Screenshotting {url} ...")
            ctx = browser.new_context(viewport={"width": 1280, "height": 900})
            page = ctx.new_page()
            try:
                page.goto(url, timeout=15000, wait_until="domcontentloaded")
                page.wait_for_timeout(1500)
                # For support chat, try to open chat widget
                if "support_chat" in key:
                    try:
                        page.click(".chat-fab, #chat-btn, .chat-button, [class*='chat']", timeout=2000)
                        page.wait_for_timeout(800)
                    except Exception:
                        pass
                page.screenshot(path=str(out_path), full_page=False)
                shots[key] = str(out_path)
                print(f"    Saved {out_path.name}")
            except Exception as e:
                print(f"    FAILED {url}: {e}")
            finally:
                ctx.close()
        browser.close()
    return shots

def compose_slide(shots: dict):
    from PIL import Image, ImageDraw, ImageFont
    import math

    # ---- slide canvas ----
    W, H = 1920, 1080
    BG = (15, 20, 35)          # dark navy
    ACCENT = (99, 179, 237)    # blue
    ACCENT2 = (252, 129, 74)   # orange
    WHITE = (255, 255, 255)
    GRAY = (160, 170, 190)
    GREEN = (72, 199, 142)
    YELLOW = (250, 204, 21)

    slide = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(slide)

    # ---- font helper ----
    def font(size, bold=False):
        candidates = [
            "C:/Windows/Fonts/segoeui.ttf" if not bold else "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/arial.ttf" if not bold else "C:/Windows/Fonts/arialbd.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
        for p in candidates:
            if Path(p).exists():
                try:
                    return ImageFont.truetype(p, size)
                except Exception:
                    pass
        return ImageFont.load_default()

    def text_centered(draw, text, x, y, fnt, fill):
        bbox = draw.textbbox((0, 0), text, font=fnt)
        tw = bbox[2] - bbox[0]
        draw.text((x - tw // 2, y), text, font=fnt, fill=fill)

    def wrap_text(draw, text, x, y, max_w, fnt, fill, line_h=22):
        words = text.split()
        line = ""
        for w in words:
            test = (line + " " + w).strip()
            bbox = draw.textbbox((0, 0), test, font=fnt)
            if bbox[2] - bbox[0] > max_w and line:
                draw.text((x, y), line, font=fnt, fill=fill)
                y += line_h
                line = w
            else:
                line = test
        if line:
            draw.text((x, y), line, font=fnt, fill=fill)

    # ---- header bar ----
    draw.rectangle([0, 0, W, 80], fill=(22, 30, 52))
    draw.rectangle([0, 77, W, 82], fill=ACCENT)
    draw.text((44, 16), "Slide 7", font=font(18), fill=GRAY)
    text_centered(draw, "What These Websites Look Like", W // 2, 22, font(30, bold=True), WHITE)
    draw.text((W - 200, 26), "Scammer4U  •  2026", font=font(18), fill=GRAY)

    # ---- layout: 2 rows × 2 cols of screenshots ----
    MARGIN = 36
    LABEL_H = 38
    BADGE_H = 30
    GAP = 18
    HEADER_H = 82
    FOOTER_H = 120

    avail_w = W - 2 * MARGIN - GAP
    avail_h = H - HEADER_H - FOOTER_H - 2 * MARGIN - GAP - 2 * LABEL_H - 2 * BADGE_H
    cell_w = avail_w // 2
    cell_h = avail_h // 2

    cells = [
        # (col, row, key, label, badge_text, badge_color)
        (0, 0, "phishing_clone",       "① Phishing Clone",       "CRITICAL · typosquat domain", ACCENT2),
        (1, 0, "github_phish_scarcity","② Scarcity / Urgency",   "🔥 Only 3 seats left!", YELLOW),
        (0, 1, "support_chat",         "③ Fake Support Chat",    "CONVERSATIONAL DECEPTION", ACCENT),
        (1, 1, None,                   "④ Sibling Pair — single axis diff",  "PRESSURE  vs  NONE", GREEN),
    ]

    for col, row, key, label, badge, badge_color in cells:
        x0 = MARGIN + col * (cell_w + GAP)
        y0 = HEADER_H + MARGIN + row * (cell_h + GAP + LABEL_H + BADGE_H)

        # label strip above image
        draw.rectangle([x0, y0, x0 + cell_w, y0 + LABEL_H], fill=(30, 40, 65))
        draw.text((x0 + 10, y0 + 9), label, font=font(16, bold=True), fill=WHITE)

        y_img = y0 + LABEL_H

        if key and key in shots:
            img_path = shots[key]
            try:
                img = Image.open(img_path).convert("RGB")
                img = img.resize((cell_w, cell_h), Image.LANCZOS)
                slide.paste(img, (x0, y_img))
            except Exception as e:
                draw.rectangle([x0, y_img, x0 + cell_w, y_img + cell_h], fill=(35, 45, 70))
                draw.text((x0 + 10, y_img + cell_h // 2), f"[screenshot failed: {e}]", font=font(13), fill=GRAY)
        elif key is None:
            # sibling pair: stack parent + child side by side
            half_w = (cell_w - 4) // 2
            for side_key, side_label in [("github_phish_parent", "Parent (control)"), ("github_phish_scarcity", "Sibling +scarcity")]:
                sx = x0 + (0 if side_key == "github_phish_parent" else half_w + 4)
                draw.rectangle([sx, y_img, sx + half_w, y_img + cell_h], fill=(30, 40, 65))
                if side_key in shots:
                    try:
                        img = Image.open(shots[side_key]).convert("RGB")
                        img = img.resize((half_w, cell_h), Image.LANCZOS)
                        slide.paste(img, (sx, y_img))
                    except Exception:
                        pass
                # sub-label at bottom of each half
                draw.rectangle([sx, y_img + cell_h - 26, sx + half_w, y_img + cell_h], fill=(0,0,0,180))
                sub_fnt = font(13, bold=True)
                bb = draw.textbbox((0,0), side_label, font=sub_fnt)
                tx = sx + (half_w - (bb[2]-bb[0])) // 2
                draw.text((tx, y_img + cell_h - 22), side_label, font=sub_fnt, fill=WHITE)
            # arrow between them
            ax = x0 + half_w + 2
            ay = y_img + cell_h // 2
            draw.line([(ax - 2, ay), (ax + 6, ay)], fill=ACCENT, width=2)
        else:
            draw.rectangle([x0, y_img, x0 + cell_w, y_img + cell_h], fill=(35, 45, 70))
            draw.text((x0 + 10, y_img + cell_h // 2), "[screenshot not available]", font=font(13), fill=GRAY)

        # thin border
        draw.rectangle([x0, y_img, x0 + cell_w, y_img + cell_h], outline=ACCENT, width=2)

        # badge below image
        y_badge = y_img + cell_h + 4
        bc = badge_color if isinstance(badge_color, tuple) else (99,179,237)
        draw.rectangle([x0, y_badge, x0 + cell_w, y_badge + BADGE_H], fill=bc)
        bb = draw.textbbox((0,0), badge, font=font(13, bold=True))
        tx = x0 + (cell_w - (bb[2]-bb[0])) // 2
        draw.text((tx, y_badge + 7), badge, font=font(13, bold=True), fill=(15,20,35))

    # ---- footer ----
    fy = H - FOOTER_H + 10
    draw.rectangle([0, H - FOOTER_H, W, H], fill=(22, 30, 52))
    draw.rectangle([0, H - FOOTER_H, W, H - FOOTER_H + 3], fill=ACCENT)

    bullets = [
        ("FIDELITY CHECK:", "1–5 visual-believability rating vs real PhishTank screenshots — number reported in §5 before submission.", ACCENT),
        ("AUTHORSHIP:",     "Templated environments authored to spec by the research team (LLM-assisted scaffolding + per-site human review). Not scraped from real attackers.", ACCENT2),
        ("COVERAGE:",       "12 attack vectors · 91 environments · 44 archetypes + 47 axis-controlled siblings. Each env wraps a legitimate-looking task around the attack trap.", GREEN),
    ]
    by = fy + 4
    for title, body, col in bullets:
        draw.text((44, by), title, font=font(14, bold=True), fill=col)
        bb = draw.textbbox((0,0), title, font=font(14, bold=True))
        draw.text((44 + bb[2] + 6, by), body, font=font(14), fill=GRAY)
        by += 26

    # ---- save ----
    out = ROOT / "slide7.png"
    slide.save(str(out), "PNG", optimize=False)
    print(f"\n  Slide saved → {out}")
    return str(out)


if __name__ == "__main__":
    print("=== Starting servers ===")
    start_servers()
    try:
        print("\n=== Taking screenshots ===")
        shots = take_screenshots()
        print(f"  Got {len(shots)} screenshot(s): {list(shots.keys())}")
        print("\n=== Composing slide ===")
        out = compose_slide(shots)
        print(f"\nDone: {out}")
    finally:
        print("\n=== Stopping servers ===")
        stop_servers()
