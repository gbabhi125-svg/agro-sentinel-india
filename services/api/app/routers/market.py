from fastapi import APIRouter

from ..market import agmarknet

router = APIRouter(prefix="/api/market", tags=["market"])


@router.get("/price/{crop}")
def price(crop: str):
    return agmarknet.current_price(crop)


@router.get("/forecast/{crop}")
def forecast(crop: str):
    return agmarknet.forecast_price(crop)
