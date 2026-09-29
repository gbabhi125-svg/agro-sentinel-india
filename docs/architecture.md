# AgroSentinel — rebuild architecture

## Status

Working end-to-end and verified in this environment: honest ML pipeline,
FastAPI backend (all routers), Next.js mobile-first frontend (all 7 pages),
Crop Doctor's full photo → questions → diagnosis → feedback loop tested
through the actual UI with Playwright. See "What's verified" below for
exactly what was and wasn't testable here.

`backend/`, `frontend/`, `ml_models/` are the old mini-project — untouched,
kept only for reference. Nothing here imports from them.

```
services/api/    FastAPI backend, one router per feature (doctor, farm, water, market, schemes, risk)
ml/              retraining pipeline + model registry (ml/registry/v1)
knowledge/       causes, observations, per-crop profiles, schemes — curated, source-linked
docs/            this file, model_card.md, viva notes (TODO)
tests/           14 pytest tests: reasoning engine, farm models, irrigation math
apps/web/        Next.js PWA-style frontend (Home, Doctor, Farm, Water, Market, Schemes, History)
```

## What's verified (in this sandbox)

- `ml/training/train.py` runs clean, produces the numbers in `docs/model_card.md`.
- `pytest tests/api` — 14/14 pass.
- FastAPI server starts clean; every route was exercised by hand (including
  a real image upload through Crop Doctor).
- `npm run build` in `apps/web` compiles with zero errors/warnings; all 7
  routes return 200; the full Doctor flow (photo → 3 questions → diagnosis →
  feedback → persisted history) was driven end-to-end with Playwright,
  screenshotted in light/dark mode and in Hindi.

## What's NOT verified here, and why

This sandbox's outbound network is allow-listed and does not include
`api.open-meteo.com` or `api.data.gov.in` (blocked with a policy 403, not a
bug in the code). That means:
- Live weather (irrigation planner, proactive risk alerts, Crop Doctor's
  weather signal) could not be tested against the real API from here.
- Live mandi prices and the price forecast could not be tested against
  data.gov.in from here (also needs `DATA_GOV_IN_API_KEY`, which isn't set).

Both fail soft with an explicit `available:false` / HTTP 503 + reason
instead of fabricated data — that behavior IS verified (see the curl output
in the commit history / conversation). They should work as soon as this
runs somewhere with normal internet access (your machine, Render, Railway,
Vercel) — nothing about the blocked calls is sandbox-specific code.

## Known coverage limits (honest, not hidden)

- Crop Doctor has full named disease/pest profiles for only 10 of 55 crops
  (`knowledge/crops/crop_profiles.json`). Every other crop still gets a
  diagnosis, capped at the generic cause level, and the API says so.
- 3 languages (English/Hindi/Kannada) are wired for UI chrome only — dynamic
  backend text (advice, disease names) is still English-only.
- "Offline mode" is a localStorage cache of the last diagnosis, not a full
  installable PWA with a service worker.
- No real trained photo classifier yet (`doctor/vision.py` is HSV colour-
  bucket analysis, documented as a weak hint, not a CNN).
- The "bigger addition" subsystems from the plan (KVK/WhatsApp escalation,
  neighbor alerts, marketplace link, insurance claim helper, village
  dashboard, SMS/IVR) are not started — each needs an external account,
  partnership, or dataset the assistant can't obtain on its own (see the
  APIs list given earlier in this conversation).

## Setup

```
# backend
cd services/api
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 ../../ml/training/train.py   # regenerates ml/registry/v1 (models are gitignored-size-safe but you can retrain any time)
uvicorn app.main:app --reload --port 8000

# frontend (separate terminal)
cd apps/web
npm install
echo "NEXT_PUBLIC_API_URL=http://127.0.0.1:8000" > .env.local
npm run dev
```

Copy root `.env.example` to `.env` and fill in `DATA_GOV_IN_API_KEY` for
real mandi prices — see the API list earlier in this conversation for where
to get each key and which phase needs it.
