"""
Firebase Cloud Messaging via the modern HTTP v1 API (the legacy server-key
API this project's earlier notes assumed is long since shut down by Google —
v1 needs a service account, not a server key).

Needs, in .env:
  FIREBASE_SERVICE_ACCOUNT_JSON   - path to the service account JSON file
                                     downloaded from Firebase console ->
                                     Project settings -> Service accounts ->
                                     Generate new private key
  FIREBASE_PROJECT_ID             - the Firebase project ID

Not tested live in this sandbox: fcm.googleapis.com is not reachable through
this session's egress policy, and no real service account is configured
here. Verify on your machine/deployment.
"""
import json
import os

import httpx

_SCOPES = ["https://www.googleapis.com/auth/firebase.messaging"]


def fcm_configured() -> bool:
    return bool(os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON") and os.environ.get("FIREBASE_PROJECT_ID"))


def _access_token() -> str:
    # Imported lazily so google-auth is only required when FCM is actually used.
    from google.auth.transport.requests import Request
    from google.oauth2 import service_account

    creds = service_account.Credentials.from_service_account_file(
        os.environ["FIREBASE_SERVICE_ACCOUNT_JSON"], scopes=_SCOPES
    )
    creds.refresh(Request())
    return creds.token


def send_alert(device_token: str, title: str, body: str, data: dict | None = None) -> dict:
    if not fcm_configured():
        return {"sent": False, "reason": "Firebase is not configured "
                                          "(FIREBASE_SERVICE_ACCOUNT_JSON / FIREBASE_PROJECT_ID)"}
    try:
        token = _access_token()
    except Exception as e:
        return {"sent": False, "reason": f"Could not mint Firebase access token: {e}"}

    project_id = os.environ["FIREBASE_PROJECT_ID"]
    url = f"https://fcm.googleapis.com/v1/projects/{project_id}/messages:send"
    payload = {
        "message": {
            "token": device_token,
            "notification": {"title": title, "body": body},
            "data": {k: str(v) for k, v in (data or {}).items()},
        }
    }
    try:
        r = httpx.post(url, headers={"Authorization": f"Bearer {token}"}, json=payload, timeout=8.0)
        r.raise_for_status()
        return {"sent": True, "response": r.json()}
    except Exception as e:
        return {"sent": False, "reason": f"FCM send failed: {e}"}
