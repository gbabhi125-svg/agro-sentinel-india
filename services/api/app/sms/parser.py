"""
Minimal keyword protocol for the SMS fallback: a farmer texts a crop name
followed by short symptom codes, e.g. "RICE YELLOWOLD SPOTS WILTDRY". This is
necessarily a much smaller slice of Crop Doctor than the app gives — no
photo, no adaptive follow-up questions (an SMS back-and-forth for 3 rounds
is a bad experience), just a single-shot best guess from whatever codes are
given, or a clear "not enough info, text HELP for codes" reply.
"""
from ..doctor.reasoning import diagnose

SYMPTOM_CODES = {
    "YELLOWOLD": "yellowing_older_leaves",
    "YELLOWNEW": "yellowing_new_leaves",
    "SPOTS": "brown_spots_with_halo",
    "WHITE": "white_powdery_coating",
    "WILTDRY": "wilting_dry_soil",
    "WILTWET": "wilting_moist_soil",
    "HOLES": "holes_in_leaves",
    "CURL": "leaf_curling",
    "BUGS": "visible_insects",
    "STICKY": "sticky_residue",
    "STUNTED": "stunted_growth",
    "BROWNEDGE": "leaf_edges_browning",
}

HELP_TEXT = (
    "AgroSentinel SMS codes: reply with CROP then codes, e.g. RICE YELLOWOLD WILTDRY. "
    "Codes: " + ", ".join(SYMPTOM_CODES.keys())
)


def parse_and_diagnose(body: str) -> str:
    tokens = body.strip().upper().split()
    if not tokens:
        return HELP_TEXT
    if tokens[0] == "HELP":
        return HELP_TEXT

    crop = tokens[0].title()
    answers = {}
    asked = set()
    for tok in tokens[1:]:
        obs_id = SYMPTOM_CODES.get(tok)
        if obs_id:
            answers[obs_id] = True
            asked.add(obs_id)

    if not answers:
        return f"No symptom codes recognised for {crop}. " + HELP_TEXT

    result = diagnose(crop, answers, weather={}, photo_hints={}, asked=asked)

    if result["status"] == "need_more_info":
        # SMS has no back-and-forth loop here — report the leading guess honestly as tentative.
        guess = result["current_leading_guess"]
        return (f"{crop}: not enough info for a confident answer yet. "
                f"Leading guess: {guess['name']} ({round(guess['probability']*100)}%). "
                f"See a KVK officer, or text more codes: " + HELP_TEXT)
    if result["status"] == "uncertain":
        top = result["top_candidates"][0]
        return f"{crop}: not confident enough to say. Closest guess: {top['name']}. Please see a KVK officer."

    name = result.get("specific_name") or result["cause_name"]
    return (f"{crop}: likely {name} ({round(result['confidence']*100)}% confidence). "
            f"{result['advice'][0]}")
