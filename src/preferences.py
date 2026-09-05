import re
from dataclasses import dataclass, field


@dataclass
class Preferences:

    budget: float = None

    min_playtime: float = None

    gaming: bool = None

    anc: bool = None

    enc: bool = None

    connectivity: str = None

    priorities: list = field(
        default_factory=list
    )


def _extract_number(text):

    numbers = re.findall(
        r"\d+(?:\.\d+)?",
        text
    )

    if not numbers:
        return None

    return float(numbers[0])


def extract_preferences(text):

    text_lower = text.lower()

    preferences = Preferences()

    # ---------------------------------------------------------
    # BUDGET
    # ---------------------------------------------------------

    # ---------------------------------------------------------
# BUDGET
# ---------------------------------------------------------
    budget_patterns = [
    r"under\s*(?:₹|rs\.?|inr|rupees?)?\s*(\d+(?:\.\d+)?)",
    r"below\s*(?:₹|rs\.?|inr|rupees?)?\s*(\d+(?:\.\d+)?)",
    r"within\s*(?:₹|rs\.?|inr|rupees?)?\s*(\d+(?:\.\d+)?)",
    r"budget\s*(?:of|is|:)?\s*(?:₹|rs\.?|inr|rupees?)?\s*(\d+(?:\.\d+)?)",
    r"₹\s*(\d+(?:\.\d+)?)",
    r"\brs\.?\s*(\d+(?:\.\d+)?)",
    r"\binr\s*(\d+(?:\.\d+)?)",
    r"\brupees?\s*(\d+(?:\.\d+)?)"
]

    for pattern in budget_patterns:
        match = re.search(pattern, text_lower)

        if match:
            preferences.budget = float(match.group(1))
            break
    # ---------------------------------------------------------
    # PLAYTIME
    # ---------------------------------------------------------

    playtime_patterns = [
        r"(\d+)\s*\+?\s*hours?",
        r"(\d+)\s*\+?\s*hrs?",
        r"battery.*?(\d+)",
        r"playtime.*?(\d+)"
    ]

    for pattern in playtime_patterns:

        match = re.search(
            pattern,
            text_lower
        )

        if match:

            preferences.min_playtime = float(
                match.group(1)
            )

            break

    # ---------------------------------------------------------
    # GAMING
    # ---------------------------------------------------------

    if (
        "gaming" in text_lower
        or "for gaming" in text_lower
    ):

        preferences.gaming = True

        preferences.priorities.append(
            "gaming"
        )

    # ---------------------------------------------------------
    # ANC
    # ---------------------------------------------------------

    if (
        "anc" in text_lower
        or "active noise cancellation"
        in text_lower
    ):

        if not any(
            phrase in text_lower
            for phrase in [
                "no anc",
                "without anc",
                "don't need anc",
                "dont need anc"
            ]
        ):

            preferences.anc = True
            preferences.priorities.append(
                "anc"
            )

    # ---------------------------------------------------------
    # ENC
    # ---------------------------------------------------------

    if (
        "enc" in text_lower
        or "environmental noise cancellation"
        in text_lower
    ):

        if not any(
            phrase in text_lower
            for phrase in [
                "no enc",
                "without enc",
                "don't need enc",
                "dont need enc"
            ]
        ):

            preferences.enc = True
            preferences.priorities.append(
                "enc"
            )

    # ---------------------------------------------------------
    # CONNECTIVITY
    # ---------------------------------------------------------

    if "bluetooth" in text_lower:

        preferences.connectivity = (
            "Bluetooth"
        )

    # ---------------------------------------------------------
    # LATENCY
    # ---------------------------------------------------------

    if (
        "latency" in text_lower
        or "low lag" in text_lower
        or "lag" in text_lower
    ):

        preferences.priorities.append(
            "latency"
        )

    # ---------------------------------------------------------
    # BATTERY PRIORITY
    # ---------------------------------------------------------

    if (
        "battery" in text_lower
        or "playtime" in text_lower
    ):

        preferences.priorities.append(
            "playtime"
        )

    # ---------------------------------------------------------
    # PRICE PRIORITY
    # ---------------------------------------------------------

    if preferences.budget is not None:

        preferences.priorities.append(
            "price"
        )

    # Remove duplicates
    preferences.priorities = list(
        dict.fromkeys(
            preferences.priorities
        )
    )

    return preferences