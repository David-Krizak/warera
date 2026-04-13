from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ResourceStat:
    raw: str
    current: Optional[float]
    max: Optional[float]
    rate: Optional[float]


@dataclass(frozen=True)
class GameStats:
    health: ResourceStat
    eating: ResourceStat
    energy: ResourceStat
    selfwork: ResourceStat
    money: Optional[int]
    level: Optional[int]