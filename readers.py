from __future__ import annotations

import re
from typing import Optional

from playwright.sync_api import Page, Locator

from game_selectors import (
    USER_MENU_SELECTOR,
    LEVEL_SELECTOR,
    MONEY_SELECTOR,
    HEALTH_ICON_D,
    EATING_ICON_D,
    ENERGY_ICON_D,
    SELFWORK_ICON_D,
)
from models import GameStats, ResourceStat


def extract_numbers(text: str) -> list[float]:
    matches = re.findall(r"\d+(?:[.,]\d+)?", text)
    nums: list[float] = []

    for m in matches:
        normalized = m.replace(",", ".")
        try:
            nums.append(float(normalized))
        except ValueError:
            pass

    return nums


def parse_int_like(text: Optional[str]) -> Optional[int]:
    if not text:
        return None

    m = re.search(r"\d+", text.replace(".", "").replace(",", ""))
    if not m:
        return None

    try:
        return int(m.group(0))
    except ValueError:
        return None


def parse_money(text: Optional[str]) -> Optional[int]:
    if not text:
        return None

    raw = text.strip().replace(" ", "").replace("\xa0", "")
    raw = re.sub(r"[^0-9.,]", "", raw)

    if not raw:
        return None

    if "." in raw and "," not in raw:
        parts = raw.split(".")
        if len(parts) > 1 and all(len(p) == 3 for p in parts[1:]):
            raw = "".join(parts)
    elif "," in raw and "." not in raw:
        parts = raw.split(",")
        if len(parts) > 1 and all(len(p) == 3 for p in parts[1:]):
            raw = "".join(parts)
        else:
            raw = raw.replace(",", "")
    else:
        raw = raw.replace(".", "").replace(",", "")

    try:
        return int(raw)
    except ValueError:
        return None


def get_text(page: Page, selector: str, timeout: int = 5000) -> Optional[str]:
    try:
        loc = page.locator(selector).first
        loc.wait_for(state="visible", timeout=timeout)
        return loc.inner_text().strip()
    except Exception:
        return None


def get_stat_block_by_icon(page: Page, icon_d: str, timeout: int = 5000) -> Optional[Locator]:
    try:
        icon = page.locator(f'{USER_MENU_SELECTOR} svg path[d="{icon_d}"]').first
        icon.wait_for(state="visible", timeout=timeout)

        block = icon.locator("xpath=ancestor::div[@aria-haspopup='dialog'][1]")
        if block.count() == 0:
            return None

        return block
    except Exception:
        return None


def get_stat_from_icon(page: Page, icon_d: str) -> Optional[ResourceStat]:
    block = get_stat_block_by_icon(page, icon_d)
    if block is None:
        return None

    try:
        text = block.inner_text().strip()
    except Exception:
        return None

    nums = extract_numbers(text)

    return ResourceStat(
        raw=text,
        current=nums[0] if len(nums) > 0 else None,
        max=nums[1] if len(nums) > 1 else None,
        rate=nums[2] if len(nums) > 2 else None,
    )


def get_health(page: Page) -> Optional[ResourceStat]:
    return get_stat_from_icon(page, HEALTH_ICON_D)


def get_eating(page: Page) -> Optional[ResourceStat]:
    return get_stat_from_icon(page, EATING_ICON_D)


def get_energy(page: Page) -> Optional[ResourceStat]:
    return get_stat_from_icon(page, ENERGY_ICON_D)


def get_selfwork(page: Page) -> Optional[ResourceStat]:
    return get_stat_from_icon(page, SELFWORK_ICON_D)


def get_money(page: Page) -> Optional[int]:
    raw = get_text(page, MONEY_SELECTOR)
    return parse_money(raw)


def get_level(page: Page) -> Optional[int]:
    raw = get_text(page, LEVEL_SELECTOR)
    return parse_int_like(raw)


def get_all_stats(page: Page) -> Optional[GameStats]:
    health = get_health(page)
    eating = get_eating(page)
    energy = get_energy(page)
    selfwork = get_selfwork(page)

    if health is None or eating is None or energy is None or selfwork is None:
        return None

    money = get_money(page)
    level = get_level(page)

    return GameStats(
        health=health,
        eating=eating,
        energy=energy,
        selfwork=selfwork,
        money=money,
        level=level,
    )


def debug_icon_stats(page: Page) -> None:
    mapping = [
        ("health", HEALTH_ICON_D),
        ("eating", EATING_ICON_D),
        ("energy", ENERGY_ICON_D),
        ("selfwork", SELFWORK_ICON_D),
    ]

    for name, icon_d in mapping:
        block = get_stat_block_by_icon(page, icon_d, timeout=2000)
        if block is None:
            print(f"[DEBUG] {name}: block not found")
            continue

        try:
            print(f"[DEBUG] {name}: {block.inner_text().strip()!r}")
        except Exception as e:
            print(f"[DEBUG] {name}: failed to read block: {e}")