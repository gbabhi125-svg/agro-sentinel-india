"""
Real mandi prices from data.gov.in's Agmarknet resource. No fabricated
fallback: if the API key is missing, the call fails, or no records match,
this returns available=False with a reason — never a made-up "₹2000
national MSP" for a crop that has no MSP, which is what the old app did.

Needs DATA_GOV_IN_API_KEY in the environment (see root .env.example).
"""
import os
import statistics
from datetime import datetime

import httpx

RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"
RESOURCE_URL = f"https://api.data.gov.in/resource/{RESOURCE_ID}"

# crop key (as used elsewhere in this app) -> exact Agmarknet commodity name
COMMODITY_MAP = {
    "rice": "Rice", "wheat": "Wheat", "maize": "Maize", "onion": "Onion",
    "potato": "Potato", "cotton(lint)": "Cotton", "groundnut": "Groundnut",
    "soyabean": "Soyabean", "sugarcane": "Sugarcane", "banana": "Banana",
    "gram": "Bengal Gram(Gram)(Whole)", "arhar/tur": "Arhar (Tur/Red Gram)(Whole)",
    "moong(green gram)": "Green Gram (Moong)(Whole)", "urad": "Black Gram (Urad Beans)(Whole)",
    "mustard": "Mustard", "sesamum": "Sesamum(Sesame,Gingelly,Til Seed)",
    "turmeric": "Turmeric", "ginger": "Ginger(Green)", "garlic": "Garlic",
    "tomato": "Tomato",
}


def _api_key() -> str | None:
    return os.environ.get("DATA_GOV_IN_API_KEY") or None


def _commodity_name(crop: str) -> str | None:
    return COMMODITY_MAP.get(crop.strip().lower())


def fetch_records(commodity: str, limit: int = 100, timeout: float = 8.0) -> dict:
    key = _api_key()
    if not key:
        return {"available": False, "reason": "DATA_GOV_IN_API_KEY is not configured"}
    try:
        r = httpx.get(RESOURCE_URL, params={
            "api-key": key, "format": "json", "limit": limit,
            "filters[commodity]": commodity,
        }, timeout=timeout)
        r.raise_for_status()
        records = r.json().get("records", [])
        return {"available": True, "records": records}
    except Exception as e:
        return {"available": False, "reason": f"Agmarknet request failed: {e}"}


def current_price(crop: str) -> dict:
    commodity = _commodity_name(crop)
    if commodity is None:
        return {"available": False, "reason": f"'{crop}' is not in this app's Agmarknet commodity map yet"}

    result = fetch_records(commodity, limit=20)
    if not result["available"]:
        return result

    prices = [float(r["modal_price"]) for r in result["records"]
              if r.get("modal_price") not in (None, "", "0") and float(r["modal_price"]) > 0]
    if not prices:
        return {"available": False, "reason": f"No live price records returned for {commodity} today"}

    rec0 = result["records"][0]
    return {
        "available": True, "crop": crop, "commodity": commodity,
        "price": round(statistics.mean(prices)), "unit": "Rs/quintal",
        "market_count": len(prices), "sample_market": rec0.get("market"), "sample_state": rec0.get("state"),
        "date": rec0.get("arrival_date"), "source": "data.gov.in Agmarknet (live)",
    }


def forecast_price(crop: str, horizons_days=(30, 60, 90)) -> dict:
    """Simple linear trend + residual-based interval over the most recent
    records available from Agmarknet — an honest 'best estimate with a
    range', not a confident single number."""
    commodity = _commodity_name(crop)
    if commodity is None:
        return {"available": False, "reason": f"'{crop}' is not in this app's Agmarknet commodity map yet"}

    result = fetch_records(commodity, limit=200)
    if not result["available"]:
        return result

    points = []
    for r in result["records"]:
        try:
            price = float(r["modal_price"])
            d = datetime.strptime(r["arrival_date"], "%d/%m/%Y")
            if price > 0:
                points.append((d, price))
        except (ValueError, KeyError, TypeError):
            continue

    if len(points) < 10:
        return {"available": False, "reason": f"Only {len(points)} usable price points for {commodity} — "
                                                "too few for a trend forecast (need at least 10)"}

    points.sort(key=lambda t: t[0])
    t0 = points[0][0]
    xs = [(d - t0).days for d, _ in points]
    ys = [p for _, p in points]
    n = len(xs)
    mean_x, mean_y = sum(xs) / n, sum(ys) / n
    var_x = sum((x - mean_x) ** 2 for x in xs)
    slope = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys)) / var_x if var_x else 0.0
    intercept = mean_y - slope * mean_x
    residuals = [y - (slope * x + intercept) for x, y in zip(xs, ys)]
    std = statistics.pstdev(residuals) if len(residuals) > 1 else 0.0
    last_x = xs[-1]

    forecast = []
    for h in horizons_days:
        point = slope * (last_x + h) + intercept
        forecast.append({
            "days_ahead": h, "point_estimate": round(point),
            "low": round(max(0, point - std)), "high": round(point + std),
        })

    return {
        "available": True, "crop": crop, "commodity": commodity,
        "n_price_points": n, "date_range": [points[0][0].isoformat(), points[-1][0].isoformat()],
        "forecast": forecast, "unit": "Rs/quintal",
        "method": "linear trend over recent Agmarknet records, +-1 std dev of residuals as the range",
        "disclaimer": "A trend line, not a guarantee — mandi prices can move sharply on local supply/demand.",
    }
