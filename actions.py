from __future__ import annotations

import json
import random
import re
import time
from dataclasses import asdict
from pathlib import Path

from playwright.sync_api import Page

from game_selectors import (
    USER_MENU_SELECTOR,
    BATTLES_ICON_D,
    FIRST_BATTLE_LINK,
    ATTACK_BUTTON,
    DEFEND_BUTTON,
    BATTLE_GEAR_PANEL_XPATH,
)
from models import GearStatus


def _click_battles_nav(page: Page) -> None:
    page.locator(USER_MENU_SELECTOR).first.wait_for(state="visible", timeout=15000)
    icon_path = page.locator(f'{USER_MENU_SELECTOR} svg path[d="{BATTLES_ICON_D}"]').first
    icon_path.wait_for(state="attached", timeout=15000)

    target = icon_path.locator("xpath=ancestor::*[@role='button' or @aria-haspopup='dialog' or self::button][1]")
    if target.count() > 0:
        target.first.click(timeout=15000)
    else:
        icon_path.locator("xpath=ancestor::*[name()='svg'][1]").first.click(timeout=15000)


def _open_first_battle(page: Page, settle_seconds: float) -> None:
    # If already inside battle view, keep current page.
    if page.locator(ATTACK_BUTTON).first.count() > 0 or page.locator(DEFEND_BUTTON).first.count() > 0:
        return

    _click_battles_nav(page)
    time.sleep(settle_seconds)
    first_battle = page.locator(FIRST_BATTLE_LINK).first
    first_battle.wait_for(state="visible", timeout=15000)
    first_battle.click(timeout=15000)
    time.sleep(settle_seconds)


def _parse_last_percent(text: str) -> int | None:
    matches = re.findall(r"(\d+)\s*%", text)
    return int(matches[-1]) if matches else None


def _parse_last_int(text: str) -> int | None:
    matches = re.findall(r"\b\d+\b", text)
    return int(matches[-1]) if matches else None


def _section(text: str, label: str, next_labels: list[str]) -> str:
    start = text.find(label)
    if start < 0:
        return ""
    end = len(text)
    for nl in next_labels:
        idx = text.find(nl, start + len(label))
        if idx != -1:
            end = min(end, idx)
    return text[start:end]


def _read_gear_from_battle_panel(page: Page) -> GearStatus:
    panel = page.locator(BATTLE_GEAR_PANEL_XPATH).first
    panel.wait_for(state="visible", timeout=15000)
    text = panel.inner_text()

    weapon = _section(text, "Weapon", ["Ammo", "Helmet", "Chest", "Pants", "Boots", "Gloves"])
    ammo = _section(text, "Ammo", ["Helmet", "Chest", "Pants", "Boots", "Gloves"])
    helmet = _section(text, "Helmet", ["Chest", "Pants", "Boots", "Gloves"])
    chest = _section(text, "Chest", ["Pants", "Boots", "Gloves"])
    pants = _section(text, "Pants", ["Boots", "Gloves"])
    boots = _section(text, "Boots", ["Gloves"])
    gloves = _section(text, "Gloves", [])

    return GearStatus(
        weapon_durability=_parse_last_percent(weapon),
        ammo_count=_parse_last_int(ammo),
        helmet_durability=_parse_last_percent(helmet),
        chest_durability=_parse_last_percent(chest),
        pants_durability=_parse_last_percent(pants),
        boots_durability=_parse_last_percent(boots),
        gloves_durability=_parse_last_percent(gloves),
    )


def _save_gear_snapshot_and_validate(page: Page) -> None:
    gear = _read_gear_from_battle_panel(page)
    Path("state").mkdir(exist_ok=True)
    Path("state/gear_status.json").write_text(json.dumps(asdict(gear), indent=2), encoding="utf-8")

    durability_values = [
        gear.weapon_durability,
        gear.helmet_durability,
        gear.chest_durability,
        gear.pants_durability,
        gear.boots_durability,
        gear.gloves_durability,
    ]
    if any(v is not None and v < 10 for v in durability_values):
        raise RuntimeError("Stopped: at least one gear durability is below 10%")
    if gear.ammo_count is None or gear.ammo_count <= 0:
        raise RuntimeError("Stopped: no ammo left")


def _read_side_percent(page: Page, side: str) -> int:
    selector = ATTACK_BUTTON if side == "attack" else DEFEND_BUTTON
    loc = page.locator(selector).first
    loc.wait_for(state="visible", timeout=10000)
    text = loc.inner_text()
    match = re.search(r"([+-]?\d+)\s*%", text)
    if not match:
        raise RuntimeError(f"Stopped: cannot parse {side} percentage from '{text}'")
    return int(match.group(1))


def _choose_side(page: Page) -> str:
    attack = _read_side_percent(page, "attack")
    defend = _read_side_percent(page, "defend")
    return "attack" if attack >= defend else "defend"


def _hit(page: Page, side: str, *, hit_sleep_min_seconds: int, hit_sleep_max_seconds: int) -> None:
    selector = ATTACK_BUTTON if side == "attack" else DEFEND_BUTTON
    button = page.locator(selector).first
    button.wait_for(state="visible", timeout=10000)
    if not button.is_enabled():
        raise RuntimeError(f"Stopped: {side} button is disabled (grayed out)")
    button.click(timeout=10000)
    time.sleep(random.randint(hit_sleep_min_seconds, hit_sleep_max_seconds))


def perform_action(
    page: Page,
    action: str,
    *,
    ui_settle_seconds: float = 2.0,
    hit_sleep_min_seconds: int = 1,
    hit_sleep_max_seconds: int = 5,
) -> None:
    if action != "battle":
        print(f"[ACTION] Unknown action: {action}")
        return

    _open_first_battle(page, settle_seconds=ui_settle_seconds)
    time.sleep(ui_settle_seconds)
    _save_gear_snapshot_and_validate(page)
    time.sleep(ui_settle_seconds)
    side = _choose_side(page)
    time.sleep(ui_settle_seconds)
    _hit(
        page,
        side,
        hit_sleep_min_seconds=hit_sleep_min_seconds,
        hit_sleep_max_seconds=hit_sleep_max_seconds,
    )
