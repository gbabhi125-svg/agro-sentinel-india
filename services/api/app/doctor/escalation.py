"""
Real "connect to an expert" escalation via Meta's WhatsApp Cloud API — chosen
over Twilio because it's official, direct (no platform markup), and free for
the volume this app needs (first 1,000 service conversations/month). See
docs/architecture.md for why Twilio/TextBee/Green API were not used here.

Needs, in .env:
  META_WHATSAPP_TOKEN       - permanent or long-lived access token
  META_PHONE_NUMBER_ID      - the WhatsApp Business phone number ID to send from
  ESCALATION_WHATSAPP_TO    - the KVK/helpline WhatsApp number to notify (E.164, no '+')

Known limitation: WhatsApp only allows a business to freely send a plain text
message within a 24h window of the recipient last messaging it, or the KVK/
helpline number to send a farmer-initiated message. Outside that window, Meta
requires a pre-approved message TEMPLATE. This sends plain text and is meant
for a helpline number that already messages the business account (or for
init/dev testing with Meta's test number) — a production deployment beyond a
single pilot KVK contact should register a template. Not tested live in this
sandbox: graph.facebook.com is blocked by this session's egress policy
(confirmed 403 from the proxy) — verify on your machine/deployment.
"""
import os

import httpx

GRAPH_API_VERSION = "v20.0"


def escalation_configured() -> bool:
    return bool(
        os.environ.get("META_WHATSAPP_TOKEN")
        and os.environ.get("META_PHONE_NUMBER_ID")
        and os.environ.get("ESCALATION_WHATSAPP_TO")
    )


def build_escalation_text(crop: str, result: dict) -> str:
    if result.get("status") == "uncertain":
        candidates = ", ".join(f"{c['name']} ({round(c['probability']*100)}%)" for c in result.get("top_candidates", []))
        return (
            f"AgroSentinel escalation — {crop}\n"
            f"App could not confidently diagnose this case. Top guesses: {candidates}.\n"
            f"Farmer needs an expert opinion — please advise."
        )
    return (
        f"AgroSentinel escalation — {crop}\n"
        f"Diagnosed as {result.get('specific_name') or result.get('cause_name')} "
        f"({round(result.get('confidence', 0) * 100)}% confidence). Escalate if: {result.get('escalate_if')}"
    )


def send_whatsapp_escalation(crop: str, result: dict, farmer_contact: str | None = None) -> dict:
    if not escalation_configured():
        return {"sent": False, "reason": "Meta WhatsApp Cloud API is not configured "
                                          "(META_WHATSAPP_TOKEN / META_PHONE_NUMBER_ID / ESCALATION_WHATSAPP_TO)"}

    token = os.environ["META_WHATSAPP_TOKEN"]
    phone_number_id = os.environ["META_PHONE_NUMBER_ID"]
    to = os.environ["ESCALATION_WHATSAPP_TO"]

    text = build_escalation_text(crop, result)
    if farmer_contact:
        text += f"\nFarmer contact: {farmer_contact}"

    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{phone_number_id}/messages"
    try:
        r = httpx.post(
            url,
            headers={"Authorization": f"Bearer {token}"},
            json={"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": text}},
            timeout=8.0,
        )
        r.raise_for_status()
        return {"sent": True, "response": r.json()}
    except Exception as e:
        return {"sent": False, "reason": f"WhatsApp send failed: {e}"}
