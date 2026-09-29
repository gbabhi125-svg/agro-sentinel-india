import json

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ..context import weather as weather_client
from ..doctor import reasoning, vision
from ..doctor.reasoning import OBSERVATIONS
from ..schemas import FeedbackRequest
from ..storage import db

router = APIRouter(prefix="/api/doctor", tags=["doctor"])


@router.get("/observations")
def observations():
    return {"observations": list(OBSERVATIONS.values())}


@router.post("/diagnose")
async def diagnose(
    crop: str = Form(...),
    answers_json: str = Form("{}"),
    asked_json: str = Form("[]"),
    state: str | None = Form(None),
    latitude: float | None = Form(None),
    longitude: float | None = Form(None),
    image: UploadFile | None = File(None),
):
    try:
        answers = json.loads(answers_json)
        asked = set(json.loads(asked_json))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="answers_json/asked_json must be valid JSON")

    photo_hints, photo_warnings = {}, []
    if image is not None:
        content = await image.read()
        vresult = vision.analyze_image(content)
        if "error" in vresult:
            raise HTTPException(status_code=400, detail=vresult["error"])
        photo_hints = vresult["photo_hints"]
        photo_warnings = vresult["quality_warnings"]

    if latitude is not None and longitude is not None:
        lat, lon = latitude, longitude
    else:
        lat, lon = weather_client.coords_for_state(state or "default")
    current = weather_client.get_current(lat, lon)
    weather = {} if current.get("unavailable") else {
        "temperature_c": current["temperature_c"], "humidity_pct": current["humidity_pct"],
        "recent_rain_mm": current["precipitation_mm"],
    }

    result = reasoning.diagnose(crop, answers, weather, photo_hints, asked)
    result["photo_quality_warnings"] = photo_warnings
    result["weather_used"] = weather if weather else {"unavailable": True, "reason": current.get("reason")}

    if result["status"] == "diagnosed":
        result["diagnosis_id"] = db.save_diagnosis(crop, result)
    return result


@router.get("/history")
def history(limit: int = 50):
    return {"history": db.list_history(limit)}


@router.post("/feedback/{diagnosis_id}")
def feedback(diagnosis_id: str, req: FeedbackRequest):
    result = db.submit_feedback(diagnosis_id, req.improved, req.notes)
    if not result["ok"]:
        raise HTTPException(status_code=404, detail=result["reason"])
    return result
