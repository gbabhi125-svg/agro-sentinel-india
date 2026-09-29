"""
Safety gate: the app must never recommend a specific pesticide/fungicide
product or active ingredient unless a real agronomist has verified it for
that exact cause (nothing in knowledge/ is marked verified yet, so today
this always blocks). This module both filters any advice text before it
reaches a farmer and is unit-tested against the knowledge base itself, so a
future content edit can't slip a chemical name in unnoticed.
"""
import re

# Common active ingredients / product classes sold in India. Not exhaustive —
# treat this as a tripwire, not a complete deny-list.
_CHEMICAL_TERMS = [
    "chlorpyrifos", "glyphosate", "mancozeb", "imidacloprid", "carbendazim",
    "malathion", "cypermethrin", "copper oxychloride", "captan", "propiconazole",
    "monocrotophos", "endosulfan", "deltamethrin", "thiamethoxam", "acephate",
    "profenofos", "quinalphos", "dimethoate", "metalaxyl", "hexaconazole",
    "difenoconazole", "azoxystrobin", "fipronil", "lambda-cyhalothrin",
    "pesticide brand", "spray this chemical",
]
_PATTERN = re.compile("|".join(re.escape(t) for t in _CHEMICAL_TERMS), re.IGNORECASE)


def contains_chemical_name(text: str) -> bool:
    return bool(_PATTERN.search(text or ""))


def assert_advice_is_safe(advice_items: list[str]) -> None:
    for item in advice_items:
        if contains_chemical_name(item):
            raise ValueError(
                f"Safety gate violation: advice text names a specific chemical: {item!r}. "
                "Only an agronomist-verified entry (none exist yet) may do this."
            )


_ESCALATION_MESSAGES = {
    "en": ("I'm not confident enough to name a specific chemical treatment, and this app never "
           "guesses on that. Please show these photos and answers to your nearest Krishi Vigyan "
           "Kendra (KVK) or agriculture extension officer before applying anything."),
    "hi": ("मुझे किसी खास रासायनिक उपचार का नाम बताने लायक भरोसा नहीं है, और यह ऐप कभी अंदाज़े से "
           "नहीं बताता। कृपया कुछ भी लगाने से पहले ये फोटो और जवाब अपने नज़दीकी कृषि विज्ञान केंद्र "
           "(केवीके) या कृषि विस्तार अधिकारी को दिखाएँ।"),
    "kn": ("ನಿರ್ದಿಷ್ಟ ರಾಸಾಯನಿಕ ಚಿಕಿತ್ಸೆಯ ಹೆಸರು ಹೇಳುವಷ್ಟು ನನಗೆ ಖಚಿತತೆ ಇಲ್ಲ, ಮತ್ತು ಈ ಆ್ಯಪ್ ಎಂದಿಗೂ "
           "ಊಹೆಯಿಂದ ಹೇಳುವುದಿಲ್ಲ. ಏನನ್ನಾದರೂ ಹಚ್ಚುವ ಮೊದಲು ದಯವಿಟ್ಟು ಈ ಫೋಟೋಗಳು ಮತ್ತು ಉತ್ತರಗಳನ್ನು "
           "ನಿಮ್ಮ ಹತ್ತಿರದ ಕೃಷಿ ವಿಜ್ಞಾನ ಕೇಂದ್ರ (ಕೆವಿಕೆ) ಅಥವಾ ಕೃಷಿ ವಿಸ್ತರಣಾ ಅಧಿಕಾರಿಗೆ ತೋರಿಸಿ."),
    "ta": ("ஒரு குறிப்பிட்ட ரசாயன சிகிச்சையை பெயரிடும் அளவுக்கு எனக்கு நம்பிக்கை இல்லை, இந்த ஆப் "
           "ஒருபோதும் யூகிக்காது. எதையும் பயன்படுத்தும் முன் இந்த புகைப்படங்களையும் பதில்களையும் "
           "உங்கள் அருகிலுள்ள கிருஷி விஞ்ஞான் கேந்திரா (கேவிகே) அல்லது வேளாண் விரிவாக்க அதிகாரியிடம் காட்டவும்."),
    "te": ("ఒక నిర్దిష్ట రసాయన చికిత్సను పేర్కొనేంత నమ్మకం నాకు లేదు, మరియు ఈ యాప్ ఎప్పుడూ ఊహించి "
           "చెప్పదు. దేనినైనా పూయడానికి ముందు దయచేసి ఈ ఫోటోలు మరియు జవాబులను మీ సమీప కృషి విజ్ఞాన "
           "కేంద్రం (కెవికె) లేదా వ్యవసాయ విస్తరణ అధికారికి చూపించండి."),
    "ml": ("ഒരു നിർദ്ദിഷ്ട രാസ ചികിത്സയുടെ പേര് പറയാൻ മാത്രം എനിക്ക് ഉറപ്പില്ല, ഈ ആപ്പ് ഒരിക്കലും "
           "ഊഹിച്ച് പറയില്ല. എന്തെങ്കിലും പ്രയോഗിക്കുന്നതിന് മുമ്പ് ഈ ഫോട്ടോകളും ഉത്തരങ്ങളും നിങ്ങളുടെ "
           "അടുത്തുള്ള കൃഷി വിജ്ഞാന കേന്ദ്രത്തിനോ (കെവികെ) കാർഷിക വിപുലീകരണ ഓഫീസർക്കോ കാണിക്കുക."),
}


def escalation_message(lang: str = "en") -> str:
    return _ESCALATION_MESSAGES.get(lang, _ESCALATION_MESSAGES["en"])
