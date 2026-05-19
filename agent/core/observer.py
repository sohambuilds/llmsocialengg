"""
Builds observation dicts from the current browser state.
The observation is what gets fed to the VLM each step.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Optional

from .browser import BrowserWrapper


@dataclass
class Observation:
    current_url: str            # Agent-facing (domain-masked, e.g. http://apply-to-g00gle-jobs.com/...)
    page_title: str
    open_tabs: list[dict]       # tabs[i]["url"] is also masked
    interactive_elements: list[dict]
    screenshot_base64: Optional[str] = None
    raw_url: str = ""           # Raw localhost URL — for pii_tracker / scorer attribution.
                                # Never goes to the LLM. Falls back to current_url
                                # if unset (legacy callers / non-localhost pages).

    def to_text(self, include_screenshot_note: bool = True) -> str:
        """Format observation as text for the VLM context."""
        lines = [
            f"Current URL: {self.current_url}",
            f"Page Title: {self.page_title}",
            "",
            f"Open Tabs ({len(self.open_tabs)}):",
        ]
        for tab in self.open_tabs:
            marker = " (active)" if tab["url"] == self.current_url else ""
            lines.append(f"  [{tab['index']}] {tab['title']} - {tab['url']}{marker}")

        lines.append("")
        lines.append(f"Interactive Elements ({len(self.interactive_elements)}):")
        for elem in self.interactive_elements:
            parts = [f"[{elem['id']}]", f"<{elem['tag']}>"]
            if elem.get("type"):
                parts.append(f"type={elem['type']}")
            if elem.get("role"):
                parts.append(f"role={elem['role']}")
            if elem.get("label"):
                parts.append(f'label="{elem["label"][:60]}"')
            if elem.get("placeholder"):
                parts.append(f'placeholder="{elem["placeholder"]}"')
            if elem.get("value"):
                parts.append(f'value="{elem["value"]}"')
            if elem.get("checked") is not None:
                parts.append(f'checked={elem["checked"]}')
            if elem.get("text"):
                text = elem["text"][:60]
                parts.append(f'"{text}"')
            if elem.get("options"):
                opts = elem["options"]
                selected = [o for o in opts if o.get("selected")]
                opt_summary = ", ".join(f'{o["value"]}="{o["text"]}"' for o in opts[:6])
                if len(opts) > 6:
                    opt_summary += f" (+{len(opts)-6} more)"
                parts.append(f"options=[{opt_summary}]")
                if selected:
                    parts.append(f'selected="{selected[0]["value"]}"')
            lines.append("  " + " ".join(parts))

        if include_screenshot_note:
            if self.screenshot_base64:
                lines.append("")
                lines.append("[Screenshot is attached below]")
            else:
                lines.append("")
                lines.append('[No screenshot attached. Use {"action": "screenshot"} to capture one.]')

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "current_url": self.current_url,
            "page_title": self.page_title,
            "open_tabs": self.open_tabs,
            "interactive_elements": self.interactive_elements,
        }
        if self.screenshot_base64:
            d["has_screenshot"] = True
        return d


class Observer:
    """Captures the current browser state as an Observation."""

    def __init__(self, browser: BrowserWrapper):
        self._browser = browser

    async def observe(self, include_screenshot: bool = False) -> Observation:
        # Retry on navigation race conditions (e.g. "Execution context was destroyed")
        last_exc: Optional[Exception] = None
        for attempt in range(3):
            try:
                raw_url = await self._browser.get_current_url()
                # Use the domain-masked URL for the agent's text observation
                # so it doesn't reason against `localhost:<port>`. The raw URL
                # is preserved on the Observation for scorer / pii_tracker use.
                current_url = await self._browser.get_current_url_display()
                page_title = await self._browser.get_page_title()

                tabs_raw = await self._browser.get_tabs_display()
                open_tabs = [t.to_dict() for t in tabs_raw]

                elements_raw = await self._browser.get_interactive_elements()
                interactive_elements = [e.to_dict() for e in elements_raw]

                screenshot_b64 = None
                if include_screenshot:
                    screenshot_b64 = await self._browser.take_screenshot_base64()

                return Observation(
                    current_url=current_url,
                    page_title=page_title,
                    open_tabs=open_tabs,
                    interactive_elements=interactive_elements,
                    screenshot_base64=screenshot_b64,
                    raw_url=raw_url,
                )
            except Exception as e:
                last_exc = e
                err_str = str(e)
                is_nav_race = (
                    "Execution context was destroyed" in err_str
                    or "most likely because of a navigation" in err_str
                    or "Target page, context or browser has been closed" in err_str
                )
                if attempt < 2 and is_nav_race:
                    print(f"  [observe] Navigation race on attempt {attempt + 1}, retrying after 1.5s...")
                    await asyncio.sleep(1.5)
                    continue
                raise

        raise last_exc  # unreachable but satisfies type checker
