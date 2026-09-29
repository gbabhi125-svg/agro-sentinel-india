import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "services" / "api"))

from app.water.irrigation import effective_rainfall, hargreaves_et0, plan_irrigation  # noqa: E402


def test_et0_is_higher_on_hotter_days():
    cool = hargreaves_et0(tmax_c=25, tmin_c=15, latitude_deg=20, day_of_year=180)
    hot = hargreaves_et0(tmax_c=40, tmin_c=28, latitude_deg=20, day_of_year=180)
    assert hot > cool


def test_effective_rainfall_never_exceeds_crop_need():
    assert effective_rainfall(precip_mm=200, etc_mm=5) == 5


def test_heavy_rain_reduces_but_does_not_always_zero_irrigation():
    forecast = [
        {"date": "2026-06-01", "tmax": 34, "tmin": 24, "precip_mm": 0},
        {"date": "2026-06-02", "tmax": 34, "tmin": 24, "precip_mm": 80},
    ]
    plan = plan_irrigation("Rice", None, days_since_sowing=10, latitude_deg=20, daily_forecast=forecast, area_ha=1)
    day0, day1 = plan["daily_plan"]
    assert day0["irrigation_needed_mm"] > day1["irrigation_needed_mm"]
    assert plan["total_volume_liters"] > 0


def test_dry_season_wheat_gets_real_irrigation_not_zero():
    # This is the exact bug the old calculator had: it compared a crop's whole
    # season need against ANNUAL rainfall, so wheat in a high-annual-rainfall,
    # dry-Rabi-season state could show "no irrigation needed". Here we feed it
    # a genuinely dry week and confirm it does NOT say zero.
    dry_week = [{"date": f"2026-01-{d:02d}", "tmax": 24, "tmin": 8, "precip_mm": 0} for d in range(1, 8)]
    plan = plan_irrigation("Wheat", None, days_since_sowing=40, latitude_deg=29, daily_forecast=dry_week, area_ha=1)
    assert plan["total_irrigation_mm"] > 0
