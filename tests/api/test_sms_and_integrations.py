import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "services" / "api"))

from app.doctor import escalation  # noqa: E402
from app.notifications import fcm  # noqa: E402
from app.sms import textbee  # noqa: E402
from app.sms.parser import HELP_TEXT, parse_and_diagnose  # noqa: E402


def test_sms_help_returns_code_list():
    assert parse_and_diagnose("HELP") == HELP_TEXT
    assert parse_and_diagnose("") == HELP_TEXT


def test_sms_unknown_crop_codes_still_replies_something_useful():
    reply = parse_and_diagnose("XYZCROP QQQQQ")
    assert "No symptom codes recognised" in reply


def test_sms_clear_case_gives_a_short_confident_reply():
    reply = parse_and_diagnose("WHEAT WHITE SPOTS")
    assert "Wheat" in reply
    assert "%" in reply  # confidence is stated, not hidden


def test_escalation_fails_soft_without_config(monkeypatch):
    for var in ("META_WHATSAPP_TOKEN", "META_PHONE_NUMBER_ID", "ESCALATION_WHATSAPP_TO"):
        monkeypatch.delenv(var, raising=False)
    result = escalation.send_whatsapp_escalation("Rice", {"status": "uncertain", "top_candidates": []})
    assert result["sent"] is False
    assert "not configured" in result["reason"]


def test_fcm_fails_soft_without_config(monkeypatch):
    monkeypatch.delenv("FIREBASE_SERVICE_ACCOUNT_JSON", raising=False)
    monkeypatch.delenv("FIREBASE_PROJECT_ID", raising=False)
    result = fcm.send_alert("tok", "title", "body")
    assert result["sent"] is False


def test_textbee_fails_soft_without_config(monkeypatch):
    monkeypatch.delenv("TEXTBEE_API_KEY", raising=False)
    monkeypatch.delenv("TEXTBEE_DEVICE_ID", raising=False)
    result = textbee.send_sms("+910000000000", "hi")
    assert result["sent"] is False
