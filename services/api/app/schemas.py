from datetime import datetime

from pydantic import BaseModel, Field


class FarmPredictRequest(BaseModel):
    state: str
    crop: str
    season: str
    year: int = Field(default_factory=lambda: datetime.now().year)
    rainfall_mm: float
    fertilizer_kg: float = 0.0
    pesticide_kg: float = 0.0


class IrrigationRequest(BaseModel):
    crop: str
    category: str | None = None
    days_since_sowing: int = 0
    state: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    area_ha: float = 1.0
    forecast_days: int = 7


class SchemesRequest(BaseModel):
    crop: str | None = None
    drought_risk: str | None = None
    land_ha: float | None = None


class DiagnoseRequest(BaseModel):
    crop: str
    answers: dict[str, bool] = {}
    asked: list[str] = []
    state: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class FeedbackRequest(BaseModel):
    improved: bool | None = None
    notes: str = ""
