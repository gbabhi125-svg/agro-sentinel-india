from fastapi import APIRouter, HTTPException

from ..farm.models import UnknownValueError, get_farm_models
from ..schemas import FarmPredictRequest
from ..storage import db

router = APIRouter(prefix="/api/farm", tags=["farm"])


@router.get("/crops")
def crops():
    return {"crops": get_farm_models().meta["crops"]}


@router.get("/states")
def states():
    return {"states": get_farm_models().meta["states"]}


@router.get("/model-card")
def model_card():
    """Honest, full validation metrics — replaces the old '100% accuracy' stat cards."""
    fm = get_farm_models()
    return {
        "validation": fm.meta["validation"], "known_issues": fm.meta["known_issues"],
        "algorithm_comparison": fm.meta.get("algorithm_comparison", {}),
        "best_algorithm": fm.meta.get("best_algorithm", {}),
    }


@router.post("/predict")
def predict(req: FarmPredictRequest):
    fm = get_farm_models()
    try:
        yield_result = fm.predict_yield(req.state, req.crop, req.season, req.year,
                                         req.rainfall_mm, req.fertilizer_kg, req.pesticide_kg)
        failure_result = fm.predict_failure(req.state, req.crop, req.season, req.year,
                                             req.rainfall_mm, req.fertilizer_kg, req.pesticide_kg)
        season_result = fm.recommend_season(req.state, req.crop, req.year, req.rainfall_mm)
        drought_result = fm.drought_risk(req.state, req.rainfall_mm)
        drought_forecast = fm.drought_early_forecast(req.state, req.crop, req.season, req.year)
    except UnknownValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "input": req.model_dump(),
        "yield": yield_result,
        "failure": failure_result,
        "season": season_result,
        "drought": drought_result,
        "drought_early_forecast": drought_forecast,
    }


@router.get("/community-alerts")
def community_alerts(state: str, crop: str, window_days: int = 14):
    """Opt-in only (plan item #9) — a report only exists here if a farmer
    ticked 'share with nearby farmers' when submitting that diagnosis."""
    reports = db.community_alerts(state, crop, window_days)
    return {"state": state, "crop": crop, "window_days": window_days, "reports": reports}
