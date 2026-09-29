"""
Open-Meteo client — free, no API key. Every function fails soft: on any
network/parse error it returns an explicit unavailable=True payload instead
of a fabricated fallback number pretending to be real weather.
"""
from datetime import date

import httpx

BASE_URL = "https://api.open-meteo.com/v1/forecast"

STATE_COORDS = {
    "andhra pradesh": (15.91, 79.74), "arunachal pradesh": (28.22, 94.73),
    "assam": (26.20, 92.94), "bihar": (25.09, 85.31), "chhattisgarh": (21.28, 81.87),
    "delhi": (28.70, 77.10), "goa": (15.30, 74.12), "gujarat": (22.25, 71.19),
    "haryana": (29.05, 76.09), "himachal pradesh": (31.10, 77.17),
    "jammu and kashmir": (33.78, 76.58), "jharkhand": (23.61, 85.28),
    "karnataka": (15.31, 75.71), "kerala": (10.85, 76.27), "madhya pradesh": (22.97, 78.65),
    "maharashtra": (19.75, 75.71), "manipur": (24.66, 93.91), "meghalaya": (25.47, 91.37),
    "mizoram": (23.16, 92.94), "nagaland": (26.16, 94.56), "odisha": (20.94, 84.80),
    "puducherry": (11.94, 79.81), "punjab": (31.14, 75.34), "sikkim": (27.53, 88.51),
    "tamil nadu": (11.13, 78.66), "telangana": (18.11, 79.02), "tripura": (23.94, 91.99),
    "uttar pradesh": (26.85, 80.95), "uttarakhand": (30.07, 79.02), "west bengal": (22.99, 87.86),
    "default": (20.59, 78.96),
}


def coords_for_state(state: str) -> tuple[float, float]:
    return STATE_COORDS.get(state.strip().lower(), STATE_COORDS["default"])


def get_current(lat: float, lon: float, timeout: float = 6.0) -> dict:
    try:
        r = httpx.get(BASE_URL, params={
            "latitude": lat, "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
            "timezone": "auto",
        }, timeout=timeout)
        r.raise_for_status()
        cur = r.json().get("current", {})
        return {
            "unavailable": False,
            "temperature_c": cur.get("temperature_2m"),
            "humidity_pct": cur.get("relative_humidity_2m"),
            "precipitation_mm": cur.get("precipitation"),
            "wind_speed_kmh": cur.get("wind_speed_10m"),
            "source": "Open-Meteo (live)",
        }
    except Exception as e:
        return {"unavailable": True, "reason": str(e), "source": "Open-Meteo"}


def get_daily_forecast(lat: float, lon: float, days: int = 7, timeout: float = 8.0) -> dict:
    """Returns daily tmax/tmin/precip for the Hargreaves ET0 calc, and an
    hourly-humidity-averaged-to-daily figure for the pest/disease risk engine."""
    try:
        r = httpx.get(BASE_URL, params={
            "latitude": lat, "longitude": lon,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
            "hourly": "relative_humidity_2m",
            "forecast_days": days, "timezone": "auto",
        }, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        daily = data.get("daily", {})
        hourly = data.get("hourly", {})
        dates = daily.get("time", [])
        tmax = daily.get("temperature_2m_max", [])
        tmin = daily.get("temperature_2m_min", [])
        precip = daily.get("precipitation_sum", [])

        humidity_by_date: dict[str, list[float]] = {}
        for ts, h in zip(hourly.get("time", []), hourly.get("relative_humidity_2m", [])):
            d = ts.split("T")[0]
            humidity_by_date.setdefault(d, []).append(h)

        days_out = []
        for i, d in enumerate(dates):
            hum = humidity_by_date.get(d, [])
            days_out.append({
                "date": d,
                "tmax": tmax[i] if i < len(tmax) else None,
                "tmin": tmin[i] if i < len(tmin) else None,
                "precip_mm": precip[i] if i < len(precip) else 0.0,
                "humidity_pct": round(sum(hum) / len(hum), 1) if hum else None,
            })
        return {"unavailable": False, "days": days_out, "source": "Open-Meteo (live)"}
    except Exception as e:
        return {"unavailable": True, "reason": str(e), "source": "Open-Meteo"}


def day_of_year(iso_date: str) -> int:
    return date.fromisoformat(iso_date).timetuple().tm_yday
