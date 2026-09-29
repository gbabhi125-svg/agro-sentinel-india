# SMS/IVR fallback — what's actually solved, and what isn't

Plan item (bigger addition #14) asked for "a basic phone-call or SMS version
of Crop Doctor" for farmers with no smartphone. Being honest about the gap
here matters as much as anywhere else in this project.

## What's built: SMS, via TextBee

`services/api/app/sms/` — a farmer texts a crop name + short symptom codes
(e.g. `RICE YELLOWOLD WILTDRY`) to a number running the TextBee Android app,
the webhook runs the same `doctor/reasoning.py` engine used by the full app
(single-shot, no adaptive follow-up questions — a 3-round SMS back-and-forth
is a bad experience), and texts back a one-line result.

**Real tradeoff, not a free lunch**: TextBee needs a spare Android phone
with an active SIM, powered on and running their app, acting as the relay.
No phone dedicated to this = no SMS fallback. `HELP` gets you the code list.

## What's NOT built: IVR (phone tree / voice)

None of the three free options discussed (TextBee, Meta WhatsApp Cloud API,
Green API/Maytapi) provide telephony — actual phone calls, voice prompts,
DTMF menu input. That needs a real telephony platform (Twilio Voice,
Exotel, Plivo, ...), which costs real money per minute and wasn't something
a free tier could cover. A farmer with a basic feature phone but no data
plan, who can't or won't type SMS codes, is still not served by anything in
this project. Don't claim otherwise in a demo or a viva — say plainly that
IVR was evaluated and set aside because every real option needed a paid
telephony account.

## If this needs to go further

- IVR: budget for Twilio Voice or Exotel (India-specific, often cheaper for
  local numbers), design a DTMF menu ("press 1 for wilting, 2 for yellow
  leaves, ..."), and expect ongoing per-minute cost — not a one-time setup.
- Better SMS UX: could add local-language keyword aliases (e.g. Hindi
  transliterations of the codes) — cheap to add, not done yet.
