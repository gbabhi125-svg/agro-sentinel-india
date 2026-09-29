"""
Real day-by-day irrigation planner using FAO-56 reference evapotranspiration
(Hargreaves-Samani method) x crop coefficient (Kc), minus effective rainfall.

This replaces the old calculator, which compared a crop's whole-SEASON water
need against ANNUAL rainfall (so a dry-season wheat crop could show "no
irrigation needed" just because the region gets plenty of rain in a
different season) and divided by a flat 120 days for every crop.
"""
import json
import math
import os
from datetime import date, timedelta

_HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(_HERE, "crop_coefficients.json"), encoding="utf-8") as f:
    _COEFF = json.load(f)


def _kc_for_crop(crop: str, category: str | None, day_in_season: int) -> float:
    row = _COEFF["crops"].get(crop) or _COEFF["category_defaults"].get(
        category or "default", _COEFF["category_defaults"]["default"]
    )
    d_ini, d_dev, d_mid, d_end = row["stage_days"]
    if day_in_season <= d_ini:
        return row["kc_ini"]
    if day_in_season <= d_ini + d_dev:
        frac = (day_in_season - d_ini) / max(d_dev, 1)
        return row["kc_ini"] + frac * (row["kc_mid"] - row["kc_ini"])
    if day_in_season <= d_ini + d_dev + d_mid:
        return row["kc_mid"]
    total = d_ini + d_dev + d_mid + d_end
    if day_in_season >= total:
        return row["kc_end"]
    frac = (day_in_season - d_ini - d_dev - d_mid) / max(d_end, 1)
    return row["kc_mid"] + frac * (row["kc_end"] - row["kc_mid"])


def hargreaves_et0(tmax_c: float, tmin_c: float, latitude_deg: float, day_of_year: int) -> float:
    """FAO-56 Hargreaves-Samani reference evapotranspiration, mm/day."""
    tmean = (tmax_c + tmin_c) / 2
    lat_rad = math.radians(latitude_deg)
    gsc = 0.0820  # MJ/m2/min, solar constant
    dr = 1 + 0.033 * math.cos(2 * math.pi * day_of_year / 365)
    delta = 0.409 * math.sin(2 * math.pi * day_of_year / 365 - 1.39)
    cos_ws = -math.tan(lat_rad) * math.tan(delta)
    cos_ws = max(-1.0, min(1.0, cos_ws))
    ws = math.acos(cos_ws)
    ra_mj = (24 * 60 / math.pi) * gsc * dr * (
        ws * math.sin(lat_rad) * math.sin(delta) + math.cos(lat_rad) * math.cos(delta) * math.sin(ws)
    )
    ra_mm = 0.408 * ra_mj
    temp_range = max(tmax_c - tmin_c, 0.1)
    et0 = 0.0023 * (tmean + 17.8) * math.sqrt(temp_range) * ra_mm
    return max(0.0, round(et0, 2))


def effective_rainfall(precip_mm: float, etc_mm: float) -> float:
    """USDA SCS-style simplification: light rain is mostly usable, heavy rain runs off."""
    if precip_mm <= 5:
        eff = precip_mm * 0.9
    elif precip_mm <= 25:
        eff = 4.5 + (precip_mm - 5) * 0.75
    else:
        eff = 19.5 + (precip_mm - 25) * 0.4
    return round(min(eff, etc_mm), 2)


def plan_irrigation(crop: str, category: str | None, days_since_sowing: int,
                     latitude_deg: float, daily_forecast: list[dict], area_ha: float = 1.0):
    """
    daily_forecast: list of {"date": "YYYY-MM-DD", "tmax": float, "tmin": float,
                              "precip_mm": float} for each upcoming day.
    Returns a day-by-day water balance, not a single seasonal guess.
    """
    days = []
    total_irrigation_mm = 0.0
    for i, day in enumerate(daily_forecast):
        d = date.fromisoformat(day["date"])
        doy = d.timetuple().tm_yday
        et0 = hargreaves_et0(day["tmax"], day["tmin"], latitude_deg, doy)
        kc = round(_kc_for_crop(crop, category, days_since_sowing + i), 2)
        etc = round(et0 * kc, 2)
        eff_rain = effective_rainfall(day.get("precip_mm", 0.0), etc)
        irrigation_mm = max(0.0, round(etc - eff_rain, 2))
        total_irrigation_mm += irrigation_mm
        days.append({
            "date": day["date"], "et0_mm": et0, "kc": kc, "crop_water_need_mm": etc,
            "effective_rainfall_mm": eff_rain, "irrigation_needed_mm": irrigation_mm,
        })

    volume_liters = round(total_irrigation_mm * area_ha * 10000)
    return {
        "crop": crop, "area_ha": area_ha,
        "days_since_sowing_at_start": days_since_sowing,
        "daily_plan": days,
        "total_irrigation_mm": round(total_irrigation_mm, 2),
        "total_volume_liters": volume_liters,
        "total_volume_m3": round(volume_liters / 1000, 1),
        "method": "FAO-56 Hargreaves-Samani ET0 x crop coefficient, minus effective rainfall (USDA SCS simplification)",
    }
