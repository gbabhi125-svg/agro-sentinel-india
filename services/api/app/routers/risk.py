from fastapi import APIRouter, Query

from ..context import weather as weather_client
from ..farm.risk_alerts import forecast_alerts
from ..notifications.fcm import send_alert
from ..schemas import SubscribeAlertRequest
from ..storage import db

router = APIRouter(prefix="/api/risk", tags=["risk"])


@router.get("/alerts")
def alerts(crop: str, state: str | None = Query(default=None),
           latitude: float | None = None, longitude: float | None = None):
    if latitude is not None and longitude is not None:
        lat, lon = latitude, longitude
    else:
        lat, lon = weather_client.coords_for_state(state or "default")
    return forecast_alerts(crop, lat, lon)


@router.post("/subscribe")
def subscribe(req: SubscribeAlertRequest):
    sub_id = db.subscribe_alert(req.device_token, req.state, req.crop)
    return {"subscription_id": sub_id}


@router.post("/notify-now/{state}/{crop}")
def notify_now(state: str, crop: str):
    """
    Checks the forecast and pushes to every device subscribed to this
    state+crop if risk is High. Meant to be called on a schedule (a daily
    cron/scheduled job at deployment time) rather than run inside the
    request/response API itself — this endpoint IS that job's entry point.
    """
    lat, lon = weather_client.coords_for_state(state)
    result = forecast_alerts(crop, lat, lon)
    if not result.get("available") or result.get("overall_alert") != "High":
        return {"notified": 0, "reason": "no high-risk alert right now", "alert_check": result}

    tokens = db.tokens_for(state, crop)
    sent = [send_alert(t, f"{crop} risk alert", f"High pest/disease risk conditions detected for {crop} in {state}.")
            for t in tokens]
    return {"notified": len(tokens), "results": sent}
