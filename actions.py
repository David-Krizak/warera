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
from readers import get_battle_percent
from models import GearStatus


def _click_icon_by_path(page: Page, icon_d: str, timeout: int = 15000) -> None:
    path = page.locator(f'{USER_MENU_SELECTOR} svg path[d="{icon_d}"]').first
    path.wait_for(state="attached", timeout=timeout)

    click_target = path.locator("xpath=ancestor::*[@role='button' or @aria-haspopup='dialog' or self::button][1]")
    if click_target.count() > 0:
        click_target.first.click(timeout=timeout)
        return

    svg_target = path.locator("xpath=ancestor::*[name()='svg'][1]")
    if svg_target.count() > 0:
        svg_target.first.click(timeout=timeout)
        return

    path.click(timeout=timeout)


def _open_battles(page: Page) -> None:
    page.locator(USER_MENU_SELECTOR).first.wait_for(state="visible", timeout=15000)
    _click_icon_by_path(page, BATTLES_ICON_D, timeout=15000)
    page.locator(FIRST_BATTLE_LINK).first.wait_for(state="visible", timeout=15000)


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


def _save_gear_snapshot(page: Page) -> None:
    gear = _read_gear_from_battle_panel(page)
    Path("state").mkdir(exist_ok=True)
    Path("state/gear_status.json").write_text(json.dumps(asdict(gear), indent=2), encoding="utf-8")

    print(f"[GEAR] weapon_durability={gear.weapon_durability}% ammo_count={gear.ammo_count}")
    print(
        "[GEAR] "
        f"helmet={gear.helmet_durability}% chest={gear.chest_durability}% "
        f"pants={gear.pants_durability}% boots={gear.boots_durability}% gloves={gear.gloves_durability}%"
    )

    durability_values = [
        gear.weapon_durability,
        gear.helmet_durability,
        gear.chest_durability,
        gear.pants_durability,
        gear.boots_durability,
        gear.gloves_durability,
    ]
    low_durability = [v for v in durability_values if v is not None and v < 10]
    if low_durability:
        raise RuntimeError("Stopped: at least one gear durability is below 10%")
    if gear.ammo_count is None or gear.ammo_count <= 0:
        raise RuntimeError("Stopped: no ammo left")


def _choose_side(page: Page) -> str:
    attack = get_battle_percent(page, "attack")
    defend = get_battle_percent(page, "defend")
    if attack is None or defend is None:
        raise RuntimeError(f"Stopped: cannot read attack/defend percentages (attack={attack}, defend={defend})")
    return "attack" if attack >= defend else "defend"


def _hit(page: Page, side: str) -> None:
    selector = ATTACK_BUTTON if side == "attack" else DEFEND_BUTTON
    button = page.locator(selector).first
    button.wait_for(state="visible", timeout=7000)

    if not button.is_enabled():
        raise RuntimeError(f"Stopped: {side} button is disabled (grayed out)")

    button.click()
    sleep_seconds = random.randint(1, 5)
    print(f"[BATTLE] Clicked {side}. Waiting {sleep_seconds}s")
    time.sleep(sleep_seconds)


def perform_action(page: Page, action: str) -> None:
    if action == "battle":
        _open_battles(page)

        first_battle = page.locator(FIRST_BATTLE_LINK).first
        first_battle.click()

        _save_gear_snapshot(page)

        side = _choose_side(page)
        _hit(page, side)
        return

    print(f"[ACTION] Unknown action: {action}")
