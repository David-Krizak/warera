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
    money: Optional[float]
    level: Optional[int]


@dataclass(frozen=True)
class GearStatus:
    weapon_durability: Optional[int]
    ammo_count: Optional[int]
    helmet_durability: Optional[int]
    chest_durability: Optional[int]
    pants_durability: Optional[int]
    boots_durability: Optional[int]
    gloves_durability: Optional[int]
