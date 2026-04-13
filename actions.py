from __future__ import annotations

import json
import random
import time
from dataclasses import asdict
from pathlib import Path

from playwright.sync_api import Page

from game_selectors import (
    USER_MENU_SELECTOR,
    BATTLES_ICON_D,
    BACKPACK_ICON_D,
    FIRST_BATTLE_LINK,
    ATTACK_BUTTON,
    DEFEND_BUTTON,
)
from readers import get_battle_percent, get_gear_status


def _open_battles(page: Page) -> None:
    battles = page.locator(f'{USER_MENU_SELECTOR} svg path[d="{BATTLES_ICON_D}"]').first
    battles.wait_for(state="visible", timeout=5000)
    battles.click()
    page.locator(FIRST_BATTLE_LINK).first.wait_for(state="visible", timeout=7000)


def _open_inventory(page: Page) -> None:
    backpack = page.locator(f'{USER_MENU_SELECTOR} svg path[d="{BACKPACK_ICON_D}"]').first
    backpack.wait_for(state="visible", timeout=5000)
    backpack.click()
    page.locator("xpath=//*[normalize-space()='Equipment']").first.wait_for(state="visible", timeout=7000)


def _save_gear_snapshot(page: Page) -> None:
    _open_inventory(page)
    gear = get_gear_status(page)
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
        _save_gear_snapshot(page)
        _open_battles(page)

        first_battle = page.locator(FIRST_BATTLE_LINK).first
        first_battle.click()

        side = _choose_side(page)
        _hit(page, side)
        return

    print(f"[ACTION] Unknown action: {action}")
