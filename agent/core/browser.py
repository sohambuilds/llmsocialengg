"""
Playwright async browser wrapper for the web navigation agent.
Manages browser lifecycle, navigation, element interaction, screenshots, and tabs.
"""

from __future__ import annotations

import asyncio
import base64
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse, urlunparse

import yaml
from playwright.async_api import async_playwright, Browser as PwBrowser, BrowserContext, Page


def _load_domain_to_port_map() -> dict[str, int]:
    """Build a domain→port lookup from environments.yaml for URL rewriting."""
    config_path = Path(__file__).parent.parent / "config" / "environments.yaml"
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
    except Exception:
        return {}

    mapping: dict[str, int] = {}
    for env in config.get("environments", {}).values():
        for site in env.get("sites", {}).values():
            domain = site.get("domain", "")
            port = site.get("port")
            if domain and port:
                mapping[domain] = port
    return mapping


_DOMAIN_TO_PORT: dict[str, int] = _load_domain_to_port_map()


def _build_port_to_domain() -> dict[int, str]:
    """Reverse of _DOMAIN_TO_PORT: port -> canonical authored domain.

    Used by the observer to mask `localhost:<port>` in the agent's
    observation so the agent reasons against a realistic-looking URL
    (e.g. `apply-to-g00gle-jobs.com`) instead of `localhost:12999`,
    which biased the agent toward false trust ("internal dev instance")
    or false defense ("not a real domain"). The browser still navigates
    to localhost; only the agent-facing URL is rewritten.
    """
    config_path = Path(__file__).parent.parent / "config" / "environments.yaml"
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
    except Exception:
        return {}

    out: dict[int, str] = {}
    for env in config.get("environments", {}).values():
        for site in env.get("sites", {}).values():
            domain = site.get("domain", "")
            port = site.get("port")
            if domain and port and port not in out:
                out[port] = domain
    return out


_PORT_TO_DOMAIN: dict[int, str] = _build_port_to_domain()
_KNOWN_LOCALHOST_PORTS: set[int] = set(_PORT_TO_DOMAIN.keys())


def _rewrite_localhost_to_domain(url: str) -> str:
    """Mask `http://localhost:<port>/<path>` as `https://<authored-domain>/<path>`.

    Drops the port and forces https. The scheme is intentionally https (not the
    raw http we actually serve on localhost) because in the real world every
    phishing clone runs behind Let's Encrypt — a typo-squat served over plain
    http would itself be a giveaway, and we saw models exploit `http://` as a
    distrust shortcut the same way they previously exploited `localhost`. The
    browser still navigates to plain-http localhost; `_rewrite_domain_to_localhost`
    coerces any scheme back to http before Playwright sees it. Returns the input
    unchanged if the URL is not a known localhost form or if the port isn't in
    our env map. Used only for what the agent sees in observations; pii_tracker /
    scorer still use the raw localhost URL for attribution.
    """
    try:
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower()
        if hostname not in ("localhost", "127.0.0.1"):
            return url
        port = parsed.port
        if port is None:
            return url
        domain = _PORT_TO_DOMAIN.get(port)
        if not domain:
            return url
        new = parsed._replace(scheme="https", netloc=domain)
        return urlunparse(new)
    except Exception:
        return url


@dataclass
class InteractiveElement:
    id: int
    tag: str
    text: str
    role: str
    element_type: Optional[str]
    placeholder: Optional[str]
    bbox: Optional[list[float]]
    is_visible: bool
    value: Optional[str] = None
    options: Optional[list[dict]] = None
    checked: Optional[bool] = None
    label: Optional[str] = None

    def to_dict(self) -> dict:
        d: dict[str, Any] = {
            "id": self.id,
            "tag": self.tag,
            "text": self.text,
        }
        if self.role:
            d["role"] = self.role
        if self.element_type:
            d["type"] = self.element_type
        if self.placeholder:
            d["placeholder"] = self.placeholder
        if self.value:
            d["value"] = self.value
        if self.label:
            d["label"] = self.label
        if self.options is not None:
            d["options"] = self.options
        if self.checked is not None:
            d["checked"] = self.checked
        if self.bbox:
            d["bbox"] = self.bbox
        return d


@dataclass
class TabInfo:
    index: int
    title: str
    url: str

    def to_dict(self) -> dict:
        return {"index": self.index, "title": self.title, "url": self.url}


class BrowserWrapper:
    """Async Playwright browser wrapper for agent interaction."""

    def __init__(self, headless: bool = True, viewport_width: int = 1280, viewport_height: int = 720):
        self._headless = headless
        self._viewport = {"width": viewport_width, "height": viewport_height}
        self._playwright = None
        self._browser: Optional[PwBrowser] = None
        self._context: Optional[BrowserContext] = None
        self._element_map: dict[int, Any] = {}
        self._file_map: dict[str, str] = {}
        # Ordered de-duplicated trail of every URL the browser has loaded
        # (driven by both explicit navigate() calls and Playwright's
        # framenavigated event so click-driven navigations are captured).
        self._visited_urls: list[str] = []
        self._visited_set: set[str] = set()
        # Cross-origin requests that escaped the localhost surface. Navigation
        # requests to non-localhost hosts are aborted at the route layer;
        # non-navigation requests (CSS/JS/fonts pulled from real CDNs) pass
        # through but are still recorded for contamination accounting.
        # Deduplicated first-seen by URL — the navigate() goto cascade and
        # browser-driven retries can hit the same target multiple times.
        self._egress_attempts: list[dict] = []
        self._egress_seen: set[str] = set()
        # Action source for egress attribution: set by execute_action() at the
        # start of each action, cleared at the end. The route handler reads
        # this so egress records can distinguish "model emitted a navigate()
        # to an external URL" (model-driven verification attempt) from "agent
        # clicked a footer social-icon" (UI fidelity decoration, accidental).
        # None means the request fired outside any agent action — e.g. during
        # the harness's initial navigate(start_url), or a page-initiated JS
        # redirect after an action settled.
        self._current_action_source: Optional[str] = None
        # Set by navigate() whenever the resolved URL points at a non-localhost
        # host that has no port mapping in environments.yaml — i.e. the agent
        # tried to "escape" to a real-internet site (https://www.ancestry.com,
        # https://workforcenow.adp.com) that we can't twin. The agent loop
        # consumes this once per step to decide whether a chrome-error landing
        # is a clean refusal (defended=True) or a noise browser error.
        self._external_nav_attempted: bool = False

    def register_files(self, file_map: dict[str, str]) -> None:
        """Register file_key -> absolute path mappings for upload actions."""
        self._file_map = file_map

    async def launch(self) -> None:
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self._headless)
        self._context = await self._browser.new_context(
            viewport=self._viewport,
            ignore_https_errors=True,
        )
        # Block cross-origin navigations before anything else hits the wire.
        # Registered on the context so it covers every page (existing + new
        # tabs opened via target="_blank").
        await self._context.route("**/*", self._egress_guard)
        # Attach navigation tracking to every page (existing + future tabs)
        # so we record URLs even when the agent clicks a link rather than
        # invoking navigate().
        self._context.on("page", self._on_new_page)
        page = await self._context.new_page()
        self._attach_nav_listener(page)

    async def close(self) -> None:
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    @property
    def _active_page(self) -> Page:
        pages = self._context.pages
        if not pages:
            raise RuntimeError("No pages open")
        return pages[-1]

    @staticmethod
    def _rewrite_domain_to_localhost(url: str) -> str:
        """Rewrite domain-based URLs to localhost using the port from environments.yaml.

        Tries the literal hostname first, then strips a leading "www." and
        retries — so navigate("https://www.linkedin.com") routes to the same
        twin as navigate("https://linkedin.com") when only the bare form is
        registered in environments.yaml.
        """
        try:
            parsed = urlparse(url)
            hostname = (parsed.hostname or "").lower()
            if hostname in ("localhost", "127.0.0.1") or not hostname:
                return url

            candidates = [hostname]
            if hostname.startswith("www.") and len(hostname) > 4:
                candidates.append(hostname[4:])

            for candidate in candidates:
                # Check if candidate:port matches a known domain (explicit port)
                if parsed.port and candidate in _DOMAIN_TO_PORT:
                    # Force http on localhost — our Flask twins serve plain
                    # HTTP only. If we keep the agent's https scheme here,
                    # Playwright lands on chrome-error://chromewebdata/ with
                    # ERR_SSL_PROTOCOL_ERROR and the agent loops trying to
                    # re-navigate.
                    new = parsed._replace(scheme="http", netloc=f"localhost:{parsed.port}")
                    rewritten = urlunparse(new)
                    print(f"  [browser] Rewrote domain URL: {parsed.scheme}://{hostname}:{parsed.port} -> http://localhost:{parsed.port}")
                    return rewritten

                # Check if candidate matches without port — use mapped port
                if candidate in _DOMAIN_TO_PORT:
                    port = _DOMAIN_TO_PORT[candidate]
                    new = parsed._replace(scheme="http", netloc=f"localhost:{port}")
                    rewritten = urlunparse(new)
                    print(f"  [browser] Rewrote domain URL: {parsed.scheme}://{hostname} -> http://localhost:{port}")
                    return rewritten

        except Exception:
            pass
        return url

    def _record_url(self, url: str) -> None:
        """Append a URL to the visited trail, deduplicated in first-seen order."""
        if not url or url == "about:blank":
            return
        if url in self._visited_set:
            return
        self._visited_set.add(url)
        self._visited_urls.append(url)

    def _on_framenavigated(self, frame) -> None:
        """Playwright callback: fires for every navigation on every frame."""
        # Only record main-frame navigations to avoid noise from analytics iframes.
        try:
            if frame.parent_frame is None:
                self._record_url(frame.url)
        except Exception:
            pass

    def _attach_nav_listener(self, page: Page) -> None:
        page.on("framenavigated", self._on_framenavigated)

    def _on_new_page(self, page: Page) -> None:
        self._attach_nav_listener(page)

    def get_visited_urls(self) -> list[str]:
        """Return the ordered, deduplicated list of URLs visited this session."""
        return list(self._visited_urls)

    async def _egress_guard(self, route) -> None:
        """Rewrite authored-domain requests to localhost; block unknown-host nav; log all egress.

        The eval surface is localhost-only. Three cases:
        1. Localhost / 127.0.0.1 — continue unchanged.
        2. Known authored domain from environments.yaml (typosquat used in
           anchor href, in-page fetch, window.location.href, server redirect) —
           rewrite to the matching localhost port via _rewrite_domain_to_localhost
           and continue. Lets cross-twin nav and same-twin click flows work
           without leaving the eval surface.
        3. Unknown external host (real-internet typos, CDNs the LLM emitted) —
           navigation requests are aborted; non-navigation requests (CSS/JS/fonts)
           continue so templates that pull from real CDNs still render. Either
           way the attempt is recorded for session metrics.
        """
        request = route.request
        url = request.url
        try:
            hostname = (urlparse(url).hostname or "").lower()
        except Exception:
            hostname = ""

        if hostname in ("localhost", "127.0.0.1", "0.0.0.0", ""):
            await route.continue_()
            return

        # Authored-domain rewrite: in-page anchor clicks, window.location.href
        # redirects, and cross-twin fetches that target a typosquat domain from
        # environments.yaml get rerouted to the matching localhost port. Mirrors
        # what navigate() does for agent-driven nav, but at the request layer so
        # it covers paths that don't go through BrowserWrapper.navigate (native
        # clicks, in-page JS). Unknown external hosts (real-internet typos, CDNs)
        # fall through to the existing block-and-log path. Playwright requires
        # the override URL to share scheme with the original; _rewrite_domain_to_localhost
        # always emits http, so we only attempt the rewrite when the original is http.
        if urlparse(url).scheme == "http":
            rewritten = self._rewrite_domain_to_localhost(url)
            if rewritten != url:
                try:
                    await route.continue_(url=rewritten)
                    return
                except Exception:
                    pass  # fall through to existing block-and-log if Playwright rejects

        is_nav = request.is_navigation_request()

        # Log every distinct (URL, blocked-or-not) once. The navigate() goto
        # cascade and browser-driven retries can hit the same target multiple
        # times; first-seen-wins keeps the trail readable.
        if url not in self._egress_seen:
            self._egress_seen.add(url)
            self._egress_attempts.append({
                "url": url,
                "hostname": hostname,
                "method": request.method,
                "resource_type": request.resource_type,
                "is_navigation": is_nav,
                "blocked": is_nav,
                "action_source": self._current_action_source,
            })
            if is_nav:
                src = self._current_action_source or "page"
                print(f"  [browser] Blocked egress navigation ({src}): {url}")

        # Routing decision is independent of dedup — every hit must be aborted
        # or continued, or Playwright will hang the request.
        if is_nav:
            try:
                await route.abort("blockedbyclient")
            except Exception:
                # Route may already be handled if the page tore down mid-request;
                # the log entry above is still the source of truth.
                pass
        else:
            try:
                await route.continue_()
            except Exception:
                pass

    def get_egress_attempts(self) -> list[dict]:
        """Return non-localhost request records (navigations blocked, asset requests passed through)."""
        return list(self._egress_attempts)

    async def navigate(self, url: str, timeout: int = 15000) -> None:
        rewritten = self._rewrite_domain_to_localhost(url)
        # Detect an unresolvable external-nav attempt: the agent asked to go
        # to a hostname we don't have a localhost twin for. The egress guard
        # will block it and the agent will land on chrome-error://. The agent
        # loop reads this flag next iteration and treats the chrome-error as
        # a clean refusal instead of a broken-page loop.
        try:
            parsed_host = (urlparse(rewritten).hostname or "").lower()
        except Exception:
            parsed_host = ""
        if parsed_host and parsed_host not in ("localhost", "127.0.0.1"):
            self._external_nav_attempted = True
            print(f"  [browser] External-nav attempt (no twin): {url} -> {rewritten}")
        url = rewritten
        self._record_url(url)
        page = self._active_page
        try:
            await page.goto(url, wait_until="networkidle", timeout=timeout)
        except Exception:
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=timeout)
            except Exception:
                try:
                    await page.goto(url, wait_until="commit", timeout=timeout)
                except Exception:
                    # Swallow nav failures here. The agent loop reads
                    # is_chrome_error_state() / consume_external_nav_attempt()
                    # on the next observation and terminates cleanly instead
                    # of bubbling a Playwright exception that aborts the batch.
                    pass
        await asyncio.sleep(0.5)

    def consume_external_nav_attempt(self) -> bool:
        """Return True if the last navigate() attempted to reach a host with
        no twin (i.e. an escape). Resets the flag, so callers see it exactly
        once."""
        flag = self._external_nav_attempted
        self._external_nav_attempted = False
        return flag

    async def is_chrome_error_state(self) -> bool:
        """True when the active page is sitting on chrome-error://chromewebdata/.

        That URL is what Playwright shows after the egress guard blocks an
        external navigation, or after an SSL handshake fails. The agent loop
        treats it as a terminal state — either a clean refusal (paired with
        consume_external_nav_attempt()) or a browser-error fail.
        """
        try:
            return (self._active_page.url or "").startswith("chrome-error://")
        except Exception:
            return False

    async def click_element(self, element_id: int) -> None:
        locator = self._element_map.get(element_id)
        if locator is None:
            raise ValueError(f"Element ID {element_id} not found in current element map")
        try:
            await locator.click(timeout=5000)
        except Exception:
            await locator.dispatch_event("click")
        await self._wait_for_stable()

    async def type_text(self, element_id: int, text: str) -> None:
        locator = self._element_map.get(element_id)
        if locator is None:
            raise ValueError(f"Element ID {element_id} not found in current element map")
        # If the target is a <select>, route to select_option instead of fill.
        # Agents sometimes emit "type" on a dropdown; fill() would raise an error
        # and abort the whole action batch. We try matching by label then by value;
        # if neither matches we leave the default selected and move on silently.
        try:
            tag = await locator.evaluate("el => el.tagName.toLowerCase()", timeout=2000)
        except Exception:
            tag = ""
        if tag == "select":
            try:
                await locator.select_option(label=text, timeout=3000)
            except Exception:
                try:
                    await locator.select_option(value=text, timeout=3000)
                except Exception:
                    pass  # keep default; don't abort the batch
            return
        try:
            await locator.click(timeout=3000)
        except Exception:
            pass
        try:
            await locator.fill(text, timeout=5000)
            return
        except Exception as primary_err:
            # Agent picked the wrong element_id (a button or label) and tried
            # to fill it. Look for a nearby real input/textarea/contenteditable
            # and retry on that — better than aborting the whole batch and
            # letting the agent loop on a stale element_id.
            fallback = await self._resolve_nearby_input_for(locator)
            if fallback is None:
                raise primary_err
            print(f"  [browser] type_text: targeted element wasn't editable; "
                  f"using nearest input/textarea")
            try:
                await fallback.click(timeout=3000)
            except Exception:
                pass
            await fallback.fill(text, timeout=5000)

    async def _resolve_nearby_input_for(self, locator) -> Optional[Any]:
        """Find a real text input/textarea/contenteditable near a clicked
        non-input element (button, label, drop-zone, etc.)."""
        page = self._active_page
        # Try descendants first
        try:
            inner = locator.locator(
                "input:not([type='hidden']):not([type='button']):not([type='submit']), "
                "textarea, [contenteditable='true']"
            ).first
            if (await inner.count()) >= 1:
                return inner
        except Exception:
            pass
        # Try the parent's other text-like inputs (e.g., a label next to its
        # input, or a button bar sharing a form with an input)
        try:
            sibling = locator.locator(
                "xpath=..//input[not(@type='hidden') and not(@type='button') and not(@type='submit')] "
                "| xpath=..//textarea "
                "| xpath=..//*[@contenteditable='true']"
            ).first
            if (await sibling.count()) >= 1:
                return sibling
        except Exception:
            pass
        # Last resort: first text-like input on the page
        try:
            page_first = page.locator(
                "input:not([type='hidden']):not([type='button']):not([type='submit']), "
                "textarea, [contenteditable='true']"
            ).first
            if (await page_first.count()) >= 1:
                return page_first
        except Exception:
            pass
        return None

    async def select_option(self, element_id: int, value: str) -> None:
        """Select an option from a <select> dropdown by value or label."""
        locator = self._element_map.get(element_id)
        if locator is None:
            raise ValueError(f"Element ID {element_id} not found in current element map")
        try:
            await locator.select_option(value=value, timeout=5000)
        except Exception:
            await locator.select_option(label=value, timeout=5000)

    async def set_checked(self, element_id: int, checked: bool) -> None:
        """Check or uncheck a checkbox/radio element."""
        locator = self._element_map.get(element_id)
        if locator is None:
            raise ValueError(f"Element ID {element_id} not found in current element map")
        await locator.set_checked(checked, timeout=5000)

    async def upload_file(self, element_id: int, file_key: str) -> None:
        """Upload a file to a file input element using a registered file key.

        Phishing sites commonly hide the real `<input type="file">` behind a
        decorative dragdrop div (`<div id="selfie-drop" onclick="document
        .getElementById('selfie-file').click()">`). The agent correctly
        targets the visible drop zone, but Playwright's set_input_files
        rejects non-input nodes. We retry on the underlying input by
        following the onclick chain or scanning the page for any
        `input[type=file]`, so the realistic dragdrop pattern doesn't break
        every env that uses it.
        """
        locator = self._element_map.get(element_id)
        if locator is None:
            raise ValueError(f"Element ID {element_id} not found in current element map")

        file_path = self._file_map.get(file_key)
        if not file_path:
            available = ", ".join(self._file_map.keys()) or "(none registered)"
            raise ValueError(f"Unknown file_key '{file_key}'. Available: {available}")
        if not os.path.exists(file_path):
            raise ValueError(f"File not found: {file_path}")

        try:
            await locator.set_input_files(file_path, timeout=5000)
            return
        except Exception as primary_err:
            # Try to resolve the actual <input type="file"> the targeted
            # element proxies for, then retry set_input_files on it.
            input_locator = await self._resolve_file_input_for(locator)
            if input_locator is None:
                raise primary_err
            print(f"  [browser] upload_file: targeted element wasn't an input; "
                  f"using associated <input type=file>")
            await input_locator.set_input_files(file_path, timeout=5000)

    async def _resolve_file_input_for(self, locator) -> Optional[Any]:
        """Find the <input type=file> that a clicked dragdrop element proxies.

        Strategy (cheapest to most expensive):
        1. The element itself, if it's already an <input type=file>.
        2. An onclick handler of the form
           `document.getElementById('X').click()` — use #X.
        3. Any descendant <input type=file> of the element.
        4. The first <input type=file> on the page (last-resort fallback;
           covers dragdrop drops with `for=` linkage or sibling layout).
        """
        page = self._active_page
        try:
            tag = (await locator.evaluate("el => el.tagName") or "").lower()
            type_attr = (await locator.get_attribute("type") or "").lower()
            if tag == "input" and type_attr == "file":
                return locator
        except Exception:
            pass

        # Parse onclick for getElementById('X').click() / .files / etc.
        try:
            onclick = await locator.get_attribute("onclick")
        except Exception:
            onclick = None
        if onclick:
            m = re.search(r"getElementById\(['\"]([^'\"]+)['\"]\)", onclick)
            if m:
                target_id = m.group(1)
                cand = page.locator(f"#{target_id}")
                try:
                    if (await cand.count()) >= 1:
                        cand_first = cand.first
                        ctag = (await cand_first.evaluate("el => el.tagName") or "").lower()
                        ctype = (await cand_first.get_attribute("type") or "").lower()
                        if ctag == "input" and ctype == "file":
                            return cand_first
                except Exception:
                    pass

        # Descendant input[type=file]
        try:
            inner = locator.locator("input[type='file']").first
            if (await inner.count()) >= 1:
                return inner
        except Exception:
            pass

        # First file input anywhere on the page
        try:
            page_first = page.locator("input[type='file']").first
            if (await page_first.count()) >= 1:
                return page_first
        except Exception:
            pass

        return None

    async def scroll(self, direction: str = "down", amount: int = 3) -> None:
        delta = amount * 300 if direction == "down" else -(amount * 300)
        await self._active_page.mouse.wheel(0, delta)
        await asyncio.sleep(0.5)

    async def take_screenshot(self) -> bytes:
        return await self._active_page.screenshot(type="png", full_page=False)

    async def take_screenshot_base64(self) -> str:
        raw = await self.take_screenshot()
        return base64.b64encode(raw).decode("utf-8")

    async def get_current_url(self) -> str:
        return self._active_page.url

    async def get_current_url_display(self) -> str:
        """Agent-facing form of the current URL.

        Maps `localhost:<port>` → the env's authored per-site domain so the
        agent reasons against a realistic URL. Chrome-error / about:blank /
        unknown ports pass through unchanged. Use this for anything that
        goes to the LLM; use get_current_url() for anything that feeds the
        scorer (pii_tracker, reached_trap).
        """
        return _rewrite_localhost_to_domain(self._active_page.url)

    async def get_page_title(self) -> str:
        return await self._active_page.title()

    async def get_tabs(self) -> list[TabInfo]:
        tabs = []
        for i, page in enumerate(self._context.pages):
            title = await page.title()
            tabs.append(TabInfo(index=i, title=title, url=page.url))
        return tabs

    async def get_tabs_display(self) -> list[TabInfo]:
        """Agent-facing tab list with masked URLs."""
        tabs = []
        for i, page in enumerate(self._context.pages):
            title = await page.title()
            tabs.append(TabInfo(index=i, title=title, url=_rewrite_localhost_to_domain(page.url)))
        return tabs

    async def switch_tab(self, tab_index: int) -> None:
        pages = self._context.pages
        if tab_index < 0 or tab_index >= len(pages):
            raise ValueError(f"Tab index {tab_index} out of range (0-{len(pages) - 1})")
        await pages[tab_index].bring_to_front()

    async def close_tab(self, tab_index: int) -> None:
        pages = self._context.pages
        if tab_index < 0 or tab_index >= len(pages):
            raise ValueError(f"Tab index {tab_index} out of range (0-{len(pages) - 1})")
        if len(pages) == 1:
            raise ValueError("Cannot close the last remaining tab")
        await pages[tab_index].close()

    async def go_back(self) -> None:
        await self._active_page.go_back(timeout=10000)
        await self._wait_for_stable()

    async def get_interactive_elements(self, max_elements: int = 60) -> list[InteractiveElement]:
        """Extract visible interactive elements from the current page."""
        page = self._active_page
        self._element_map.clear()
        elements: list[InteractiveElement] = []
        element_id = 0

        selectors = [
            "a[href]",
            "button",
            "input:not([type='hidden'])",
            "select",
            "textarea",
            "[role='button']",
            "[role='link']",
            "[role='menuitem']",
            "[role='tab']",
            "[role='checkbox']",
            "[role='radio']",
            "[onclick]",
            "[tabindex]",
        ]

        seen_handles = set()

        for selector in selectors:
            if element_id >= max_elements:
                break
            try:
                locators = page.locator(selector)
                count = await locators.count()
            except Exception:
                continue

            for i in range(min(count, max_elements - element_id)):
                try:
                    loc = locators.nth(i)
                    if not await loc.is_visible():
                        continue

                    bbox_raw = await loc.bounding_box()
                    if not bbox_raw:
                        continue
                    if bbox_raw["width"] < 5 or bbox_raw["height"] < 5:
                        continue

                    element_handle = await loc.element_handle()
                    if element_handle is None:
                        continue
                    handle_id = id(element_handle)
                    if handle_id in seen_handles:
                        continue
                    seen_handles.add(handle_id)

                    tag = await loc.evaluate("el => el.tagName.toLowerCase()")
                    text_content = await loc.evaluate(
                        "el => (el.innerText || el.textContent || el.value || el.getAttribute('aria-label') || '').trim().substring(0, 80)"
                    )
                    role = await loc.get_attribute("role") or ""
                    el_type = await loc.get_attribute("type") or ""
                    placeholder = await loc.get_attribute("placeholder") or ""
                    value = ""
                    options_list = None
                    checked_state = None
                    label_text = None

                    if tag == "select":
                        value = await loc.evaluate("el => el.value || ''")
                        options_list = await loc.evaluate("""el => {
                            return Array.from(el.options).map(o => ({
                                value: o.value,
                                text: o.text.trim().substring(0, 50),
                                selected: o.selected
                            }));
                        }""")
                    elif tag == "input" and el_type in ("checkbox", "radio"):
                        checked_state = await loc.is_checked()
                        label_text = await loc.evaluate("""el => {
                            if (el.labels && el.labels.length > 0)
                                return el.labels[0].textContent.trim().substring(0, 80);
                            let p = el.parentElement;
                            if (p && p.tagName === 'LABEL')
                                return p.textContent.trim().substring(0, 80);
                            return '';
                        }""")
                    elif tag in ("input", "textarea"):
                        value = await loc.evaluate("el => el.value || ''")
                    elif tag == "input" and el_type == "file":
                        label_text = await loc.evaluate("""el => {
                            if (el.labels && el.labels.length > 0)
                                return el.labels[0].textContent.trim().substring(0, 80);
                            return el.getAttribute('accept') || 'file upload';
                        }""")

                    bbox = [
                        round(bbox_raw["x"], 1),
                        round(bbox_raw["y"], 1),
                        round(bbox_raw["width"], 1),
                        round(bbox_raw["height"], 1),
                    ]

                    elem = InteractiveElement(
                        id=element_id,
                        tag=tag,
                        text=text_content,
                        role=role,
                        element_type=el_type if el_type else None,
                        placeholder=placeholder if placeholder else None,
                        bbox=bbox,
                        is_visible=True,
                        value=value if value else None,
                        options=options_list,
                        checked=checked_state,
                        label=label_text if label_text else None,
                    )
                    elements.append(elem)
                    self._element_map[element_id] = loc
                    element_id += 1

                except Exception:
                    continue

        return elements

    async def _wait_for_stable(self, timeout: int = 2000) -> None:
        try:
            await self._active_page.wait_for_load_state("domcontentloaded", timeout=timeout)
        except Exception:
            pass
        await asyncio.sleep(0.3)

    async def execute_action(self, action) -> None:
        """Execute an AgentAction on the browser."""
        from .action_space import AgentAction

        if not isinstance(action, AgentAction):
            raise TypeError(f"Expected AgentAction, got {type(action)}")

        # Tag any cross-origin requests fired during this action with the
        # action's type, so the egress log can later separate hallucinated
        # navigate() calls from click-through behaviour on footer anchors.
        self._current_action_source = action.action_type
        try:
            match action.action_type:
                case "click":
                    await self.click_element(action.params["element_id"])
                case "type":
                    await self.type_text(action.params["element_id"], action.params["text"])
                case "select_option":
                    await self.select_option(action.params["element_id"], action.params["value"])
                case "check":
                    await self.set_checked(action.params["element_id"], action.params["checked"])
                case "upload_file":
                    await self.upload_file(action.params["element_id"], action.params["file_key"])
                case "scroll":
                    await self.scroll(action.params["direction"], action.params["amount"])
                case "navigate":
                    await self.navigate(action.params["url"])
                case "go_back":
                    await self.go_back()
                case "switch_tab":
                    await self.switch_tab(action.params["tab_index"])
                case "close_tab":
                    await self.close_tab(action.params["tab_index"])
                case "wait":
                    await asyncio.sleep(min(action.params["seconds"], 30))
                case "screenshot" | "done":
                    pass
                case _:
                    raise ValueError(f"Unknown action type: {action.action_type}")
        finally:
            self._current_action_source = None
