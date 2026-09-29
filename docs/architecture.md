# AgroSentinel — rebuild architecture

## Status: Phase 0 (scaffold) complete

This is the target structure for the major-project rebuild. `backend/` and
`frontend/` are the existing mini-project and stay untouched until each
piece is ported and verified.

```
services/api/    FastAPI backend (replaces backend/app.py, one router per feature)
ml/              training, evaluation, model registry (replaces ml_models/train_model.py)
knowledge/       crops, causes, symptoms, schemes — curated data with source + last_verified
docs/            this file, model cards, viva notes
tests/           api, ml, e2e
apps/web/        Next.js frontend (replaces frontend/, not created yet)
```

## Phase order

0. Scaffold (this commit)
1. Honest ML retrain (no label leakage) + Crop Doctor reasoning core
2. Water/irrigation — FAO-56 daily water balance
3. Market prices + forecast (needs `DATA_GOV_IN_API_KEY`)
4. Government scheme matcher
5. i18n, dark mode, voice input, offline caching
6. Photo-classifier training, expert escalation, community alerts,
   marketplace link, SMS/IVR — each needs external accounts/partnerships,
   built only once its API/data is in hand

See root `.env.example` for which keys unlock which phase.
