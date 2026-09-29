# AgroSentinel — rebuild architecture

## Status

All core plan items plus the feasible medium/bigger additions are built and
verified end-to-end in this environment (see below for exactly what "verified"
means and what couldn't be live-tested from this sandbox).

`backend/`, `frontend/`, `ml_models/` are the old mini-project — untouched,
kept only for reference. Nothing here imports from them.

```
services/api/app/
  doctor/       vision.py, reasoning.py, safety.py, escalation.py (WhatsApp)
  farm/         models.py (yield/failure/season/drought), risk_alerts.py
  water/        irrigation.py (FAO-56 Hargreaves)
  market/       agmarknet.py (live prices + forecast)
  schemes/      matcher.py, insurance.py (PMFBY claim guide)
  notifications/ fcm.py (Firebase push, v1 API)
  sms/          textbee.py, parser.py (optional SMS fallback)
  storage/      db.py (SQLite: diagnoses, feedback, photos, community reports, alert subs)
  routers/      doctor, farm, water, market, schemes, risk, officer, sms
ml/
  training/     train.py (honest yield/failure/season pipeline), train_photo_model.py (real CNN, script only)
  registry/v1/  trained models + metadata.json + state_lpa.json
knowledge/      causes, observations, crop_profiles, schemes, insurance — curated, source-linked
docs/           this file, model_card.md, sms_ivr_note.md
tests/          22 pytest tests: reasoning, farm models, irrigation math, SMS parsing, integration config guards, photo-model smoke test
apps/web/       Next.js app — Home, Doctor (+progress), Farm, Water, Market, Schemes, History, Officer
```

## What's verified (in this sandbox)

- `ml/training/train.py` runs clean, numbers in `docs/model_card.md`.
- `pytest tests/` — 22/22 pass (reasoning engine, farm models, irrigation
  math, SMS keyword parser, escalation/FCM/TextBee fail-soft-without-config
  guards, and a real end-to-end photo-classifier training smoke test against
  synthetic images).
- FastAPI server starts clean; every route exercised by hand, including a
  full escalation → photo-history → community-alert → SMS chain with curl
  and Python `requests`.
- `npm run build` compiles with zero errors across all 9 routes. Playwright
  drove: the full Doctor flow with photo/plant-label/community opt-in →
  confident diagnosis → "Send to KVK" escalation button → feedback →
  history; the photo-progress view showing two real stored photos in order;
  the officer dashboard showing real aggregated counts; the PMFBY claim
  guide; the nearby-reports banner. Screenshotted in light/dark mode and Hindi.

## What's NOT verified here, and why

This sandbox's outbound network is allow-listed and blocks (confirmed with
403s from the egress proxy, not guessed):
`api.open-meteo.com`, `api.data.gov.in`, `graph.facebook.com` (Meta
WhatsApp Cloud API), `fcm.googleapis.com` (Firebase), `api.textbee.dev`,
`kaggle.com`, `download.pytorch.org`.

That means live weather, live mandi prices, WhatsApp escalation, push
notifications, and SMS sending could not be exercised against the real
services from here. Every one of them fails soft with an explicit reason
(`available:false` / `sent:false` + why) instead of fabricated data or a
silent no-op — that fail-soft behavior IS verified (see the test suite and
the curl transcripts in the commit history). They should work as soon as
this runs somewhere with normal internet access and the real keys you now
have, in `.env` (never commit that file).

`raw.githubusercontent.com` (individual files) and PyPI ARE reachable from
here, which is how `torch`/`torchvision` got installed to mechanically
smoke-test `train_photo_model.py` — but `kaggle.com` and GitHub's bulk
download path (`codeload.github.com`) are blocked, so the real PlantVillage/
PlantDoc dataset could not be fetched here at any scale.

## Known coverage limits (honest, not hidden)

- Crop Doctor has full named disease/pest profiles for only 10 of 55 crops
  (`knowledge/crops/crop_profiles.json`). Every other crop still gets a
  diagnosis, capped at the generic cause level, and the API says so.
- 3 languages (English/Hindi/Kannada) are wired for UI chrome only — dynamic
  backend text (advice, disease names) is still English-only.
- "Offline mode" is a localStorage cache of the last diagnosis, not a full
  installable PWA with a service worker.
- No real trained photo classifier is loaded yet — `doctor/vision.py` is
  still HSV colour-bucket analysis. `train_photo_model.py` exists and is
  mechanically proven correct, but produces a real model only once you run
  it on your own machine against real downloaded data.
- e-NAM marketplace integration and real Soil Health Card data pulls remain
  out of reach — neither has a public self-serve API (confirmed earlier in
  this project's research); unchanged from the original assessment.
- SMS fallback needs a spare Android phone running TextBee; true IVR (phone
  tree / voice, no smartphone at all) is not solved by any free option and
  is documented as such in `docs/sms_ivr_note.md`, not silently dropped.
- Automatic recurring push alerts need a cron/scheduled job at deployment
  time calling `POST /api/risk/notify-now/{state}/{crop}` — this repo
  provides that endpoint, not the scheduler itself.

## Setup

```
# backend
cd services/api
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 ../../ml/training/train.py   # regenerates ml/registry/v1
uvicorn app.main:app --reload --port 8000

# frontend (separate terminal)
cd apps/web
npm install
echo "NEXT_PUBLIC_API_URL=http://127.0.0.1:8000" > .env.local
npm run dev
```

Copy root `.env.example` to `.env` and fill in the keys you now have —
never commit that file. `DATA_GOV_IN_API_KEY` unlocks real mandi prices;
`META_WHATSAPP_TOKEN`/`META_PHONE_NUMBER_ID`/`ESCALATION_WHATSAPP_TO` unlock
expert escalation; `FIREBASE_SERVICE_ACCOUNT_JSON`/`FIREBASE_PROJECT_ID`
unlock push alerts; `TEXTBEE_API_KEY`/`TEXTBEE_DEVICE_ID` unlock SMS (only
if you have a spare Android phone).

To train a real photo classifier once you have PlantVillage/PlantDoc
downloaded locally as an ImageFolder:
```
pip install -r ml/requirements-photo.txt
python3 ml/training/train_photo_model.py --data-dir /path/to/dataset --epochs 5
```
