import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "services" / "api"))

from app.doctor import reasoning  # noqa: E402


def _run_to_completion(crop, weather, photo_hints, truth_answers, max_q=3):
    answers, asked = {}, set()
    for _ in range(max_q + 1):
        res = reasoning.diagnose(crop, answers, weather, photo_hints, asked)
        if res["status"] != "need_more_info":
            return res
        qid = res["question"]["id"]
        asked.add(qid)
        answers[qid] = truth_answers.get(qid, False)
    return res


def test_clear_fungal_case_reaches_confident_diagnosis():
    weather = {"temperature_c": 22, "humidity_pct": 85, "recent_rain_mm": 40}
    res = _run_to_completion(
        "Wheat", weather, photo_hints={"white_powdery_coating": 0.9},
        truth_answers={"white_powdery_coating": True, "brown_spots_with_halo": True, "symptom_spreading_fast": True},
    )
    assert res["status"] == "diagnosed"
    assert res["cause_id"] == "fungal_leaf_disease"
    assert res["confidence"] >= reasoning.CONFIDENCE_FLOOR


def test_ambiguous_case_declines_to_guess():
    # hot + dry weather alone genuinely straddles water-stress and heat-stress
    weather = {"temperature_c": 36, "humidity_pct": 30, "recent_rain_mm": 0}
    res = _run_to_completion("Rice", weather, photo_hints={}, truth_answers={})
    assert res["status"] == "uncertain"
    assert "top_candidates" in res


def test_never_asks_more_than_max_questions():
    weather = {}
    answers, asked = {}, set()
    for i in range(reasoning.MAX_QUESTIONS + 5):
        res = reasoning.diagnose("Rice", answers, weather, {}, asked)
        if res["status"] != "need_more_info":
            break
        asked.add(res["question"]["id"])
        answers[res["question"]["id"]] = False
    assert len(asked) <= reasoning.MAX_QUESTIONS
    assert res["status"] in ("diagnosed", "uncertain")


def test_advice_never_contains_chemical_names():
    from app.doctor import safety
    for cause in reasoning.CAUSES.values():
        for line in cause["generic_advice"]:
            assert not safety.contains_chemical_name(line), line


def test_unresolved_crop_profile_is_explicit_not_invented():
    res = _run_to_completion(
        "Barley", {"temperature_c": 22, "humidity_pct": 85, "recent_rain_mm": 40},
        photo_hints={"white_powdery_coating": 0.9},
        truth_answers={"white_powdery_coating": True, "brown_spots_with_halo": True},
    )
    if res["status"] == "diagnosed":
        assert res["specific_name"] is None
        assert "no curated" in res["specific_name_note"]
