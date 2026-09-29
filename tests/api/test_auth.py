import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "services" / "api"))

from app.auth.security import create_access_token, decode_access_token, hash_password, verify_password  # noqa: E402


def test_password_is_never_stored_in_plaintext():
    h = hash_password("correct horse battery staple")
    assert h != "correct horse battery staple"
    assert verify_password("correct horse battery staple", h)
    assert not verify_password("wrong password", h)


def test_token_roundtrip_and_tamper_detection():
    token = create_access_token("user-42")
    assert decode_access_token(token) == "user-42"
    assert decode_access_token(token + "tampered") is None
    assert decode_access_token("not.a.token") is None


def test_long_password_does_not_crash_bcrypt():
    # bcrypt's own 72-byte limit — must not raise, matching every mainstream wrapper's behavior.
    long_password = "x" * 200
    h = hash_password(long_password)
    assert verify_password(long_password, h)
