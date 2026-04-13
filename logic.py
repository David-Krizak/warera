from __future__ import annotations

from typing import Optional

from models import GameStats


def can_do_work(stats: GameStats, min_energy: float, min_selfwork: float = 0) -> bool:
    if stats.energy.current is None:
        return False
    if stats.selfwork.current is None:
        return False

    return stats.energy.current >= min_energy and stats.selfwork.current >= min_selfwork


def choose_action(stats: Optional[GameStats]) -> Optional[str]:
    if stats is None:
        return None

    if stats.health.current is not None and stats.health.current > 0:
        return "battle"

    return None
