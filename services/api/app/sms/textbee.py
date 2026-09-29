"""
Optional SMS fallback for farmers with no smartphone, via textbee.dev — an
open-source gateway where an old Android phone with a SIM card relays SMS
through your normal mobile carrier plan (free up to 300 msgs/month). Chosen
over Twilio SMS because it needs no phone-number rental or per-message
Twilio fees; it needs a spare Android phone instead, which is a real
tradeoff, not a free lunch — see docs/architecture.md.

This is NOT a phone-tree/IVR system: it only sends and receives plain SMS
text. A farmer with no phone at all (voice-only feature phone / landline)
still isn't served — nothing free covers that, so this app doesn't claim to.

Needs, in .env:
  TEXTBEE_API_KEY     - from your textbee.dev account
  TEXTBEE_DEVICE_ID   - the Android device registered in the TextBee app

Not tested live in this sandbox (api.textbee.dev is not reachable through
this session's egress policy, and no real device is registered here).
"""
import os

import httpx

BASE_URL = "https://api.textbee.dev/api/v1"


def textbee_configured() -> bool:
    return bool(os.environ.get("TEXTBEE_API_KEY") and os.environ.get("TEXTBEE_DEVICE_ID"))


def send_sms(to: str, message: str) -> dict:
    if not textbee_configured():
        return {"sent": False, "reason": "TextBee is not configured (TEXTBEE_API_KEY / TEXTBEE_DEVICE_ID)"}

    api_key = os.environ["TEXTBEE_API_KEY"]
    device_id = os.environ["TEXTBEE_DEVICE_ID"]
    url = f"{BASE_URL}/gateway/devices/{device_id}/send-sms"
    try:
        r = httpx.post(url, headers={"x-api-key": api_key},
                        json={"recipients": [to], "message": message}, timeout=8.0)
        r.raise_for_status()
        return {"sent": True, "response": r.json()}
    except Exception as e:
        return {"sent": False, "reason": f"TextBee send failed: {e}"}
