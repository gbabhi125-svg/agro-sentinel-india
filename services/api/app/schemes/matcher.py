"""Matches curated government schemes (knowledge/schemes/schemes.json) to a farmer's situation."""
import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_PATH = os.path.join(_HERE, "..", "..", "..", "..", "knowledge", "schemes", "schemes.json")
with open(_PATH, encoding="utf-8") as f:
    SCHEMES = json.load(f)["schemes"]


def match_schemes(crop: str | None = None, drought_risk: str | None = None,
                   land_ha: float | None = None) -> list[dict]:
    results = []
    for s in SCHEMES:
        applies = s["applies_to"]
        crops = applies.get("crops")
        if crops != "all" and crop and crop not in crops:
            continue
        prefers_drought = applies.get("prefers_drought_risk")
        max_land = applies.get("max_land_ha")
        if max_land is not None and land_ha is not None and land_ha > max_land:
            continue

        relevance = 50
        if prefers_drought and drought_risk in prefers_drought:
            relevance = 90
        elif crops != "all" and crop in (crops or []):
            relevance = 80

        results.append({
            "id": s["id"], "full_name": s["full_name"], "benefit": s["benefit"],
            "eligibility": s["eligibility"], "link": s["link"], "source": s["source"],
            "last_verified": s["last_verified"], "relevance_score": relevance,
        })

    results.sort(key=lambda r: r["relevance_score"], reverse=True)
    return results
