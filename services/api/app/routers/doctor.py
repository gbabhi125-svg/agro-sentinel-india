import json
import os

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from ..auth.deps import get_current_user_optional
from ..context import weather as weather_client
from ..doctor import escalation, reasoning, vision
from ..doctor.reasoning import OBSERVATIONS, _localize_observation
from ..schemas import EscalateRequest, FeedbackRequest
from ..storage import db

router = APIRouter(prefix="/api/doctor", tags=["doctor"])


@router.get("/observations")
def observations(lang: str = "en"):
    return {"observations": [_localize_observation(obs_id, lang) for obs_id in OBSERVATIONS]}


@router.post("/diagnose")
async def diagnose(
    crop: str = Form(...),
    answers_json: str = Form("{}"),
    asked_json: str = Form("[]"),
    state: str | None = Form(None),
    latitude: float | None = Form(None),
    longitude: float | None = Form(None),
    plant_label: str | None = Form(None),
    opt_in_community: bool = Form(False),
    lang: str = Form("en"),
    image: UploadFile | None = File(None),
    user: dict | None = Depends(get_current_user_optional),
):
    try:
        answers = json.loads(answers_json)
        asked = set(json.loads(asked_json))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="answers_json/asked_json must be valid JSON")

    photo_hints, photo_warnings, photo_bytes = {}, [], None
    if image is not None:
        photo_bytes = await image.read()
        vresult = vision.analyze_image(photo_bytes)
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

    result = reasoning.diagnose(crop, answers, weather, photo_hints, asked, lang=lang)
    result["photo_quality_warnings"] = photo_warnings
    result["weather_used"] = weather if weather else {"unavailable": True, "reason": current.get("reason")}

    # Both a confident diagnosis and an "ask an expert" outcome are saved —
    # the uncertain case is exactly the one a farmer might want to escalate.
    if result["status"] in ("diagnosed", "uncertain"):
        result["diagnosis_id"] = db.save_diagnosis(
            crop, result, plant_label=plant_label, state=state,
            photo_bytes=photo_bytes, opt_in_community=opt_in_community,
            user_id=user["id"] if user else None,
        )
    return result


@router.get("/history")
def history(limit: int = 50, user: dict | None = Depends(get_current_user_optional)):
    # Logged-in farmers see only their own history; without a token (e.g. the
    # officer view or a not-logged-in dev call) this stays the old unscoped list.
    return {"history": db.list_history(limit, user_id=user["id"] if user else None)}


@router.get("/photo/{diagnosis_id}")
def photo(diagnosis_id: str):
    path = db.get_photo_path(diagnosis_id)
    if not path:
        raise HTTPException(status_code=404, detail="No photo stored for this diagnosis")
    return FileResponse(path, media_type="image/jpeg")


@router.get("/plant-labels")
def plant_labels():
    return {"labels": db.list_plant_labels()}


@router.get("/photo-progress/{plant_label}")
def photo_progress(plant_label: str):
    return {"plant_label": plant_label, "entries": db.photo_progress(plant_label)}


@router.post("/feedback/{diagnosis_id}")
def feedback(diagnosis_id: str, req: FeedbackRequest):
    result = db.submit_feedback(diagnosis_id, req.improved, req.notes)
    if not result["ok"]:
        raise HTTPException(status_code=404, detail=result["reason"])
    return result


@router.post("/escalate/{diagnosis_id}")
def escalate(diagnosis_id: str, req: EscalateRequest):
    record = db.get_diagnosis(diagnosis_id)
    if not record:
        raise HTTPException(status_code=404, detail="unknown diagnosis_id")
    return escalation.send_whatsapp_escalation(record["crop"], record["result"], req.farmer_contact)
