"""
Proactive pest/disease risk alerts — warns before the farmer notices a
problem, using the SAME weather-flag logic and crop knowledge base as the
Crop Doctor (doctor/reasoning.py), driven by a real multi-day forecast
instead of a single current reading.
"""
from ..context import weather as weather_client
from ..doctor.reasoning import CROP_PROFILES, derive_weather_flags


def forecast_alerts(crop: str, lat: float, lon: float, days: int = 5) -> dict:
    fc = weather_client.get_daily_forecast(lat, lon, days=days)
    if fc.get("unavailable"):
        return {"available": False, "reason": fc.get("reason", "weather forecast unavailable")}

    profile = CROP_PROFILES.get(crop)
    if not profile:
        return {"available": True, "crop": crop, "has_profile": False,
                "message": f"No curated pest/disease profile for {crop} yet — "
                           "general advice: watch for sudden leaf changes after heavy rain or heat spikes.",
                "daily_conditions": []}

    entries = profile.get("diseases", []) + profile.get("pests", [])
    daily_alerts = []
    for day in fc["days"]:
        flags = derive_weather_flags({
            "temperature_c": day.get("tmax"), "humidity_pct": day.get("humidity_pct"),
            "recent_rain_mm": day.get("precip_mm"),
        })
        hits = []
        for e in entries:
            match_count = sum(flags.get(rf, 0.0) for rf in e["risk_factors"])
            match_frac = match_count / len(e["risk_factors"]) if e["risk_factors"] else 0
            if match_frac >= 0.5:
                hits.append({"name": e["name"], "severity": e["severity"], "match_fraction": round(match_frac, 2)})
        daily_alerts.append({
            "date": day["date"], "tmax": day.get("tmax"), "humidity_pct": day.get("humidity_pct"),
            "precip_mm": day.get("precip_mm"), "risk_hits": hits,
        })

    any_high = any(h["severity"] == "High" for d in daily_alerts for h in d["risk_hits"])
    return {
        "available": True, "crop": crop, "has_profile": True,
        "overall_alert": "High" if any_high else ("Watch" if any(d["risk_hits"] for d in daily_alerts) else "Low"),
        "daily_conditions": daily_alerts,
        "note": "Conditions matching a pest/disease's known risk factors, not a diagnosis — "
                "use Crop Doctor once you actually see symptoms.",
    }
