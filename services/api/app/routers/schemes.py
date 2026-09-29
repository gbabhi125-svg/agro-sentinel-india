from fastapi import APIRouter

from ..schemas import SchemesRequest
from ..schemes.insurance import get_claim_guide
from ..schemes.matcher import match_schemes

router = APIRouter(prefix="/api/schemes", tags=["schemes"])


@router.post("/match")
def match(req: SchemesRequest):
    results = match_schemes(req.crop, req.drought_risk, req.land_ha)
    return {"count": len(results), "schemes": results}


@router.get("/pmfby-claim-guide")
def pmfby_claim_guide():
    return get_claim_guide()
