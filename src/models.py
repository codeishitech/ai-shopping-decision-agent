from dataclasses import dataclass, field


@dataclass
class UserPreferences:
    budget: float | None = None
    min_playtime: float | None = None

    form_factor: str | None = None
    connectivity: str | None = None
    brand: str | None = None

    gaming: bool | None = None
    anc: bool | None = None
    enc: bool | None = None

    priorities: list[str] = field(default_factory=list)