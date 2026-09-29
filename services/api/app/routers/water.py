from fastapi import APIRouter, HTTPException

from ..context import weather as weather_client
from ..schemas import IrrigationRequest
from ..water.irrigation import plan_irrigation

router = APIRouter(prefix="/api/water", tags=["water"])


@router.post("/irrigation-plan")
def irrigation_plan(req: IrrigationRequest):
    if req.latitude is not None and req.longitude is not None:
        lat, lon = req.latitude, req.longitude
    elif req.state:
        lat, lon = weather_client.coords_for_state(req.state)
    else:
        raise HTTPException(status_code=400, detail="Provide either state, or latitude+longitude")

    fc = weather_client.get_daily_forecast(lat, lon, days=req.forecast_days)
    if fc.get("unavailable"):
        raise HTTPException(status_code=503, detail=f"Weather forecast unavailable: {fc.get('reason')}")

    return plan_irrigation(req.crop, req.category, req.days_since_sowing, lat, fc["days"], req.area_ha)
