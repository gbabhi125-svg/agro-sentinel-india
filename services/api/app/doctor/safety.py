"""
Safety gate: the app must never recommend a specific pesticide/fungicide
product or active ingredient unless a real agronomist has verified it for
that exact cause (nothing in knowledge/ is marked verified yet, so today
this always blocks). This module both filters any advice text before it
reaches a farmer and is unit-tested against the knowledge base itself, so a
future content edit can't slip a chemical name in unnoticed.
"""
import re

# Common active ingredients / product classes sold in India. Not exhaustive —
# treat this as a tripwire, not a complete deny-list.
_CHEMICAL_TERMS = [
    "chlorpyrifos", "glyphosate", "mancozeb", "imidacloprid", "carbendazim",
    "malathion", "cypermethrin", "copper oxychloride", "captan", "propiconazole",
    "monocrotophos", "endosulfan", "deltamethrin", "thiamethoxam", "acephate",
    "profenofos", "quinalphos", "dimethoate", "metalaxyl", "hexaconazole",
    "difenoconazole", "azoxystrobin", "fipronil", "lambda-cyhalothrin",
    "pesticide brand", "spray this chemical",
]
_PATTERN = re.compile("|".join(re.escape(t) for t in _CHEMICAL_TERMS), re.IGNORECASE)


def contains_chemical_name(text: str) -> bool:
    return bool(_PATTERN.search(text or ""))


def assert_advice_is_safe(advice_items: list[str]) -> None:
    for item in advice_items:
        if contains_chemical_name(item):
            raise ValueError(
                f"Safety gate violation: advice text names a specific chemical: {item!r}. "
                "Only an agronomist-verified entry (none exist yet) may do this."
            )


def escalation_message() -> str:
    return (
        "I'm not confident enough to name a specific chemical treatment, and this app never "
        "guesses on that. Please show these photos and answers to your nearest Krishi Vigyan "
        "Kendra (KVK) or agriculture extension officer before applying anything."
    )
