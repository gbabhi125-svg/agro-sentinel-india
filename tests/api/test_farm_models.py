import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "services" / "api"))

from app.farm.models import UnknownValueError, get_farm_models  # noqa: E402


@pytest.fixture(scope="module")
def fm():
    return get_farm_models()


def test_unknown_crop_is_rejected_not_defaulted(fm):
    with pytest.raises(UnknownValueError):
        fm.predict_yield("Maharashtra", "Dragonfruit", "Kharif", 2019, 1000, 0, 0)


def test_yield_prediction_is_positive_and_sane(fm):
    result = fm.predict_yield("Punjab", "Wheat", "Rabi", 2019, 700, 10000, 50)
    assert result["predicted_yield"] > 0
    assert result["unit"] == "t/ha"


def test_failure_model_does_not_take_yield_as_input():
    import inspect
    sig = inspect.signature(get_farm_models().predict_failure)
    assert "yield_val" not in sig.parameters
    assert "yield_tha" not in sig.parameters


def test_perennial_crop_suppresses_season_switch_advice(fm):
    result = fm.recommend_season("Kerala", "Coconut", 2019, 3000)
    assert result["suppressed"] is True


def test_drought_rule_is_deterministic_not_a_model(fm):
    r1 = fm.drought_risk("Rajasthan", 200)
    r2 = fm.drought_risk("Rajasthan", 200)
    assert r1 == r2
    assert r1["risk_level"] == "High"  # 200mm is deep in "Scanty" territory for any Indian state's LPA

    wet = fm.drought_risk("Kerala", 3500)
    assert wet["risk_level"] == "Low"
