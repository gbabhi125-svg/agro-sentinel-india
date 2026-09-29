"""PMFBY claim helper — guidance only, not a filing integration (see the
_note in knowledge/insurance/pmfby_claim_steps.json for why no such
integration exists)."""
import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_PATH = os.path.join(_HERE, "..", "..", "..", "..", "knowledge", "insurance", "pmfby_claim_steps.json")
with open(_PATH) as f:
    CLAIM_GUIDE = json.load(f)


def get_claim_guide() -> dict:
    return CLAIM_GUIDE
