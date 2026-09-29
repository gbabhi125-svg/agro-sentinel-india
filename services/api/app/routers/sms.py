"""
Webhook for incoming SMS from TextBee. Exact payload field names are taken
from TextBee's documented webhook format at the time this was written;
confirm against your TextBee dashboard once configured, since this couldn't
be verified against a live device from this sandbox — adjust the field
lookups below if they don't match what your account actually sends.
"""
from typing import Any

from fastapi import APIRouter, Request

from ..sms.parser import parse_and_diagnose
from ..sms.textbee import send_sms

router = APIRouter(prefix="/api/sms", tags=["sms"])


def _first(d: dict, *keys: str) -> Any:
    for k in keys:
        if k in d and d[k]:
            return d[k]
    return None


@router.post("/webhook")
async def webhook(request: Request):
    payload = await request.json()
    sender = _first(payload, "sender", "from", "phoneNumber", "senderNumber")
    body = _first(payload, "message", "text", "body")

    if not sender or not body:
        return {"handled": False, "reason": "could not find sender/message in payload", "payload_keys": list(payload.keys())}

    reply = parse_and_diagnose(body)
    result = send_sms(sender, reply)
    return {"handled": True, "reply_text": reply, "send_result": result}
