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
        await self._context.new_page()

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
        """Rewrite domain-based URLs to localhost using the port from environments.yaml."""
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname or ""
            if hostname in ("localhost", "127.0.0.1") or not hostname:
                return url

            # Check if hostname:port matches a known domain (with explicit port)
            if parsed.port and hostname in _DOMAIN_TO_PORT:
                new = parsed._replace(netloc=f"localhost:{parsed.port}")
                rewritten = urlunparse(new)
                print(f"  [browser] Rewrote domain URL: {hostname}:{parsed.port} -> localhost:{parsed.port}")
                return rewritten

            # Check if hostname matches without port — use mapped port
            if hostname in _DOMAIN_TO_PORT:
                port = _DOMAIN_TO_PORT[hostname]
                new = parsed._replace(netloc=f"localhost:{port}")
                rewritten = urlunparse(new)
                print(f"  [browser] Rewrote domain URL: {hostname} -> localhost:{port}")
                return rewritten

        except Exception:
            pass
        return url

    async def navigate(self, url: str, timeout: int = 15000) -> None:
        url = self._rewrite_domain_to_localhost(url)
        page = self._active_page
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout)
        except Exception:
            await page.goto(url, wait_until="commit", timeout=timeout)

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
        try:
            await locator.click(timeout=3000)
        except Exception:
            pass
        await locator.fill(text, timeout=5000)

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
        """Upload a file to a file input element using a registered file key."""
        locator = self._element_map.get(element_id)
        if locator is None:
            raise ValueError(f"Element ID {element_id} not found in current element map")

        file_path = self._file_map.get(file_key)
        if not file_path:
            available = ", ".join(self._file_map.keys()) or "(none registered)"
            raise ValueError(f"Unknown file_key '{file_key}'. Available: {available}")
        if not os.path.exists(file_path):
            raise ValueError(f"File not found: {file_path}")

        await locator.set_input_files(file_path, timeout=5000)

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

    async def get_page_title(self) -> str:
        return await self._active_page.title()

    async def get_tabs(self) -> list[TabInfo]:
        tabs = []
        for i, page in enumerate(self._context.pages):
            title = await page.title()
            tabs.append(TabInfo(index=i, title=title, url=page.url))
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
