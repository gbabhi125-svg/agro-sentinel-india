from fastapi import APIRouter, Query

from ..context import weather as weather_client
from ..farm.risk_alerts import forecast_alerts

router = APIRouter(prefix="/api/risk", tags=["risk"])


@router.get("/alerts")
def alerts(crop: str, state: str | None = Query(default=None),
           latitude: float | None = None, longitude: float | None = None):
    if latitude is not None and longitude is not None:
        lat, lon = latitude, longitude
    else:
        lat, lon = weather_client.coords_for_state(state or "default")
    return forecast_alerts(crop, lat, lon)
