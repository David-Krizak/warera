from __future__ import annotations

from playwright.sync_api import Page


def perform_action(page: Page, action: str) -> None:
    if action == "work":
        print("[ACTION] Work would run here")
        return

    print(f"[ACTION] Unknown action: {action}")