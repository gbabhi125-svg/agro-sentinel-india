"""
Structured probabilistic reasoning over the curated knowledge base — this is
a transparent, explainable expert system (each score is traceable to which
symptom/weather signal drove it), not a black-box claim. It combines:
  - the farmer's yes/no answers (authoritative when present)
  - weak photo-colour hints (only when a question hasn't been asked yet)
  - weather signals for this crop's location
into a probability per candidate cause, asks the single most-discriminating
follow-up question when uncertain, and refuses to commit past a hard cap of
follow-up questions or below a confidence floor — see CONFIDENCE_FLOOR /
MARGIN_FLOOR / MAX_QUESTIONS below.
"""
import json
import os

from . import safety

_HERE = os.path.dirname(os.path.abspath(__file__))
_KNOWLEDGE_DIR = os.path.join(_HERE, "..", "..", "..", "..", "knowledge")

with open(os.path.join(_KNOWLEDGE_DIR, "causes", "causes.json")) as f:
    CAUSES = {c["id"]: c for c in json.load(f)}
with open(os.path.join(_KNOWLEDGE_DIR, "observations", "observations.json")) as f:
    OBSERVATIONS = {o["id"]: o for o in json.load(f)}
with open(os.path.join(_KNOWLEDGE_DIR, "crops", "crop_profiles.json")) as f:
    CROP_PROFILES = json.load(f)["profiles"]

# Safety gate runs at import time: if anyone edits causes.json to slip in a
# chemical name, the app refuses to start rather than silently serving it.
for _cause in CAUSES.values():
    safety.assert_advice_is_safe(_cause.get("generic_advice", []))

CONFIDENCE_FLOOR = 0.35
MARGIN_FLOOR = 0.12
MAX_QUESTIONS = 3


def derive_weather_flags(weather: dict) -> dict:
    """weather: {"temperature_c": float, "humidity_pct": float, "recent_rain_mm": float}"""
    flags = {}
    temp = weather.get("temperature_c")
    hum = weather.get("humidity_pct")
    rain = weather.get("recent_rain_mm")
    if temp is not None:
        flags["high_temperature"] = 1.0 if temp >= 33 else 0.0
        flags["hot_dry"] = 1.0 if temp >= 33 and (hum is not None and hum < 45) else 0.0
        flags["cool_moist"] = 1.0 if temp <= 20 and (hum is not None and hum >= 60) else 0.0
        flags["dry_warm"] = 1.0 if 25 <= temp <= 33 and (hum is not None and hum < 45) else 0.0
        flags["warm_humid"] = 1.0 if temp >= 26 and (hum is not None and hum >= 65) else 0.0
    if hum is not None:
        flags["high_humidity"] = 1.0 if hum >= 75 else 0.0
        flags["dry_weather"] = 1.0 if hum < 40 else 0.0
    if rain is not None:
        flags["recent_heavy_rain"] = 1.0 if rain >= 30 else 0.0
        flags["recent_dry_spell"] = 1.0 if rain <= 2 else 0.0
        flags["standing_water"] = 1.0 if rain >= 60 else 0.0
        flags["windy"] = 0.0  # no wind signal available yet — never true from weather alone
        flags["waterlogging"] = flags["standing_water"]
    return flags


def _evidence(obs_id: str, answers: dict, photo_hints: dict) -> float:
    if obs_id in answers and answers[obs_id] is not None:
        return 1.0 if answers[obs_id] else 0.0
    if obs_id in photo_hints:
        return min(1.0, photo_hints[obs_id]) * 0.6
    return 0.05  # small neutral prior for an unasked, unphotographed symptom


def _score_cause(cause: dict, answers: dict, photo_hints: dict, weather_flags: dict) -> float:
    symptoms = cause.get("typical_symptoms", {})
    if symptoms:
        total_w = sum(symptoms.values())
        symptom_score = sum(w * _evidence(obs, answers, photo_hints) for obs, w in symptoms.items()) / total_w
    else:
        symptom_score = 0.3

    sig = cause.get("weather_signature", {})
    weather_score = 0.5
    for key, w in sig.items():
        weather_score += w * weather_flags.get(key, 0.0) * 0.5
    weather_score = max(0.0, min(1.0, weather_score))

    return max(0.001, 0.65 * symptom_score + 0.35 * weather_score)


def _refine_named_entity(cause_id: str, crop: str, weather_flags: dict):
    """Surface a crop-specific disease/pest name under a generic cause, only
    for crops with a curated profile. Everything else stays at the generic
    cause level — no invented crop-specific names."""
    profile = CROP_PROFILES.get(crop)
    if not profile:
        return None
    candidates = [e for e in profile.get("diseases", []) + profile.get("pests", []) if e["cause_id"] == cause_id]
    if not candidates:
        return None
    scored = []
    for c in candidates:
        match = sum(weather_flags.get(rf, 0.0) for rf in c["risk_factors"])
        scored.append((match, c))
    scored.sort(key=lambda t: t[0], reverse=True)
    return scored[0][1]


def next_question(top_causes: list[dict], answers: dict, asked: set) -> dict | None:
    """Pick the unanswered observation that best separates the current top-2 causes."""
    if len(top_causes) < 1:
        return None
    top = top_causes[0]["typical_symptoms"] if top_causes else {}
    second = top_causes[1]["typical_symptoms"] if len(top_causes) > 1 else {}
    all_obs = set(top) | set(second)
    unanswered = [o for o in all_obs if o not in answers and o not in asked and o in OBSERVATIONS]
    if not unanswered:
        # fall back to the highest-weight unanswered symptom of the top cause alone
        unanswered = [o for o in top if o not in answers and o not in asked and o in OBSERVATIONS]
    if not unanswered:
        return None
    best = max(unanswered, key=lambda o: abs(top.get(o, 0) - second.get(o, 0)))
    return OBSERVATIONS[best]


def diagnose(crop: str, answers: dict, weather: dict, photo_hints: dict, asked: set | None = None) -> dict:
    asked = asked or set()
    weather_flags = derive_weather_flags(weather)

    scored = [
        {"cause_id": cid, **cause, "score": _score_cause(cause, answers, photo_hints, weather_flags)}
        for cid, cause in CAUSES.items()
    ]
    # Sharpen contrast between candidates (like softmax temperature) so a
    # clearly-matching cause isn't diluted by ten other causes' baseline
    # scores when normalized — ranking is unaffected, only spread changes.
    sharpened_total = sum(c["score"] ** 2 for c in scored)
    for c in scored:
        c["probability"] = round((c["score"] ** 2) / sharpened_total, 4)
    scored.sort(key=lambda c: c["probability"], reverse=True)

    top, second = scored[0], scored[1] if len(scored) > 1 else None
    margin = top["probability"] - (second["probability"] if second else 0.0)
    confident = top["probability"] >= CONFIDENCE_FLOOR and margin >= MARGIN_FLOOR

    if not confident and len(asked) < MAX_QUESTIONS:
        q = next_question(scored[:3], answers, asked)
        if q is not None:
            return {
                "status": "need_more_info",
                "question": q,
                "questions_asked": len(asked),
                "current_leading_guess": {"name": top["name"], "probability": top["probability"]},
            }

    if not confident:
        return {
            "status": "uncertain",
            "message": safety.escalation_message(),
            "top_candidates": [
                {"cause_id": c["cause_id"], "name": c["name"], "probability": c["probability"]}
                for c in scored[:3]
            ],
        }

    refined = _refine_named_entity(top["cause_id"], crop, weather_flags)
    return {
        "status": "diagnosed",
        "cause_id": top["cause_id"],
        "cause_name": top["name"],
        "specific_name": refined["name"] if refined else None,
        "specific_name_note": (
            f"a curated profile exists for {crop}, this is its most weather-consistent match"
            if refined else f"no curated disease/pest profile for {crop} yet — showing the general cause only"
        ),
        "confidence": top["probability"],
        "margin_over_second": round(margin, 4),
        "advice": top["generic_advice"],
        "escalate_if": top.get("escalate_if"),
        "runner_up": {"name": second["name"], "probability": second["probability"]} if second else None,
        "reasoning_method": "rule-based probabilistic scoring over curated symptom/weather evidence, "
                             "not a trained neural network — every number here is traceable to a rule.",
    }
