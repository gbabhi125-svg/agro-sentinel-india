from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import numpy as np
import os
import requests
import threading
import subprocess
import sys
from datetime import datetime

app = Flask(__name__)
CORS(app)

BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, "ml_models")

# ── Load everything ───────────────────────────────────────────
print("Loading AgroSentinel India models...")

yield_model   = joblib.load(os.path.join(MODEL_DIR, "yield_model.pkl"))
drought_model = joblib.load(os.path.join(MODEL_DIR, "drought_model.pkl"))
failure_model = joblib.load(os.path.join(MODEL_DIR, "failure_model.pkl"))
season_model  = joblib.load(os.path.join(MODEL_DIR, "season_model.pkl"))
le_state      = joblib.load(os.path.join(MODEL_DIR, "le_state.pkl"))
le_crop       = joblib.load(os.path.join(MODEL_DIR, "le_crop.pkl"))
le_season     = joblib.load(os.path.join(MODEL_DIR, "le_season.pkl"))
le_drought    = joblib.load(os.path.join(MODEL_DIR, "le_drought.pkl"))
feat_names    = joblib.load(os.path.join(MODEL_DIR, "feature_names.pkl"))
meta          = joblib.load(os.path.join(MODEL_DIR, "metadata.pkl"))

print(f"✅ Models loaded — {len(meta['crops'])} crops | {len(meta['states'])} states")

YIELD_FEAT   = feat_names['yield']
DROUGHT_FEAT = feat_names['drought']
FAILURE_FEAT = feat_names['failure']
SEASON_FEAT  = feat_names['season']

retrain_status = {"status": "idle", "message": ""}

# ── Helpers ───────────────────────────────────────────────────
def safe_enc(encoder, value, fallback=0):
    try:    return int(encoder.transform([value])[0])
    except: return fallback

RAIN = {
    "Andhra Pradesh":980,"Arunachal Pradesh":2782,"Assam":2818,
    "Bihar":1186,"Chhattisgarh":1292,"Goa":3005,"Gujarat":820,
    "Haryana":614,"Himachal Pradesh":1251,"Jharkhand":1200,
    "Karnataka":1139,"Kerala":3055,"Madhya Pradesh":1017,
    "Maharashtra":1177,"Manipur":1467,"Meghalaya":2818,
    "Mizoram":2500,"Nagaland":1900,"Odisha":1451,"Punjab":649,
    "Rajasthan":531,"Sikkim":2740,"Tamil Nadu":998,
    "Telangana":917,"Tripura":2260,"Uttar Pradesh":899,
    "Uttarakhand":1900,"West Bengal":1582,
}
STATE_COORDS = {
    "andhra pradesh":(15.91,79.74),"assam":(26.20,92.94),
    "bihar":(25.09,85.31),"gujarat":(22.25,71.19),
    "haryana":(29.05,76.09),"karnataka":(15.31,75.71),
    "kerala":(10.85,76.27),"madhya pradesh":(22.97,78.65),
    "maharashtra":(19.75,75.71),"odisha":(20.94,84.80),
    "punjab":(31.14,75.34),"rajasthan":(27.02,74.21),
    "tamil nadu":(11.12,78.65),"telangana":(18.11,79.01),
    "uttar pradesh":(26.84,80.94),"west bengal":(22.98,87.85),
    "default":(20.59,78.96),
}
FALLBACK_PRICES = {
    "rice":2200,"wheat":2350,"maize":1850,"tomato":1200,"potato":800,
    "onion":1500,"sugarcane":350,"cotton":6200,"soybean":4200,
    "groundnut":5800,"banana":1800,"mango":4500,"turmeric":8500,
    "ginger":7200,"coffee":18000,"mustard":5200,"chickpea":5500,
    "lentil":6800,"garlic":4200,"chilli":9500,"bajra":2350,
    "jowar":2738,"ragi":3578,"arhar":7000,"moong":8558,
    "urad":7400,"sesame":9000,"sunflower":6015,"jute":4500,
}
CROP_EMOJIS = {
    "Rice":"🌾","Wheat":"🌾","Maize":"🌽","Tomato":"🍅","Potato":"🥔",
    "Onion":"🧅","Banana":"🍌","Mango":"🥭","Cotton":"🌿","Coffee":"☕",
    "Sugarcane":"🎋","Groundnut":"🥜","Coconut":"🥥","Turmeric":"🫚",
    "Ginger":"🫚","Chilli":"🌶","Mustard":"🌻","Soybean":"🫘",
    "Sunflower":"🌻","Jute":"🌿","Bajra":"🌾","Jowar":"🌾",
    "Ragi":"🌾","Arhar":"🫘","Moong":"🫘","Urad":"🫘",
    "Garlic":"🧄","Sesame":"🌿","Lentil":"🫘","Chickpea":"🫘",
    "default":"🌱"
}

# ── Crop Water Requirements (mm/season) ──────────────────────
CROP_WATER_REQ = {
    "rice": {"Kharif":1200,"Rabi":900,"Summer":1400,"default":1200},
    "wheat": {"Rabi":450,"Kharif":500,"default":450},
    "maize": {"Kharif":600,"Rabi":500,"Summer":700,"default":600},
    "sugarcane": {"Kharif":1800,"Rabi":1800,"Whole Year":2000,"default":1800},
    "cotton": {"Kharif":700,"default":700},
    "tomato": {"Kharif":400,"Rabi":350,"Summer":500,"default":400},
    "potato": {"Rabi":400,"default":400},
    "onion": {"Rabi":350,"Kharif":400,"default":375},
    "banana": {"Whole Year":1800,"default":1800},
    "mango": {"Summer":800,"default":800},
    "groundnut": {"Kharif":500,"Rabi":450,"default":500},
    "soybean": {"Kharif":450,"default":450},
    "mustard": {"Rabi":250,"default":250},
    "sunflower": {"Kharif":600,"Rabi":500,"Summer":650,"default":600},
    "default": {"default":600}
}

# ── Pest & Disease Risk Data ──────────────────────────────────
PEST_RISK_DATA = {
    "rice": {
        "pests": [
            {"name":"Brown Plant Hopper","risk_factors":["high_humidity","standing_water"],"severity":"High"},
            {"name":"Stem Borer","risk_factors":["warm_temp","dense_crop"],"severity":"Medium"},
            {"name":"Leaf Folder","risk_factors":["high_humidity"],"severity":"Medium"},
        ],
        "diseases": [
            {"name":"Blast (Pyricularia)","risk_factors":["high_humidity","low_temp"],"severity":"High"},
            {"name":"Bacterial Leaf Blight","risk_factors":["flooding","wind"],"severity":"High"},
            {"name":"Sheath Blight","risk_factors":["high_humidity","dense_planting"],"severity":"Medium"},
        ]
    },
    "wheat": {
        "pests": [
            {"name":"Aphids","risk_factors":["dry_weather","low_rainfall"],"severity":"Medium"},
            {"name":"Army Worm","risk_factors":["late_sowing"],"severity":"High"},
        ],
        "diseases": [
            {"name":"Yellow Rust","risk_factors":["cool_moist"],"severity":"High"},
            {"name":"Powdery Mildew","risk_factors":["dry_warm"],"severity":"Medium"},
            {"name":"Loose Smut","risk_factors":["cool_humid"],"severity":"Medium"},
        ]
    },
    "maize": {
        "pests": [
            {"name":"Fall Army Worm","risk_factors":["warm_humid","low_rainfall"],"severity":"High"},
            {"name":"Stem Borer","risk_factors":["warm_temp"],"severity":"Medium"},
        ],
        "diseases": [
            {"name":"Turcicum Blight","risk_factors":["high_humidity","moderate_temp"],"severity":"High"},
            {"name":"Common Rust","risk_factors":["cool_moist"],"severity":"Medium"},
        ]
    },
    "tomato": {
        "pests": [
            {"name":"Whitefly","risk_factors":["hot_dry","low_humidity"],"severity":"High"},
            {"name":"Fruit Borer","risk_factors":["warm_humid"],"severity":"High"},
        ],
        "diseases": [
            {"name":"Early Blight","risk_factors":["high_humidity","warm"],"severity":"High"},
            {"name":"Late Blight","risk_factors":["cool_moist"],"severity":"High"},
            {"name":"Fusarium Wilt","risk_factors":["warm_soil","poor_drainage"],"severity":"Medium"},
        ]
    },
    "cotton": {
        "pests": [
            {"name":"Bollworm","risk_factors":["warm_humid"],"severity":"High"},
            {"name":"Whitefly","risk_factors":["hot_dry"],"severity":"High"},
            {"name":"Aphids","risk_factors":["cool_dry"],"severity":"Medium"},
        ],
        "diseases": [
            {"name":"Leaf Curl Virus","risk_factors":["high_humidity","whitefly"],"severity":"High"},
            {"name":"Bacterial Blight","risk_factors":["warm_humid","wind"],"severity":"Medium"},
        ]
    },
    "default": {
        "pests": [
            {"name":"Aphids","risk_factors":["dry_weather"],"severity":"Medium"},
            {"name":"Thrips","risk_factors":["hot_dry"],"severity":"Medium"},
        ],
        "diseases": [
            {"name":"Powdery Mildew","risk_factors":["dry_warm"],"severity":"Medium"},
            {"name":"Root Rot","risk_factors":["waterlogging","poor_drainage"],"severity":"Medium"},
        ]
    }
}

# ── Government Schemes ────────────────────────────────────────
GOVT_SCHEMES = {
    "PM-KISAN": {
        "full_name": "Pradhan Mantri Kisan Samman Nidhi",
        "benefit": "₹6,000/year direct income support in 3 installments",
        "eligibility": "All small & marginal farmers with cultivable land",
        "link": "https://pmkisan.gov.in",
        "emoji": "💰",
        "applicable_crops": "all",
        "applicable_states": "all"
    },
    "PMFBY": {
        "full_name": "Pradhan Mantri Fasal Bima Yojana",
        "benefit": "Crop insurance covering natural calamities, pests & diseases",
        "eligibility": "All farmers growing notified crops",
        "link": "https://pmfby.gov.in",
        "emoji": "🛡️",
        "applicable_crops": "all",
        "applicable_states": "all"
    },
    "PKVY": {
        "full_name": "Paramparagat Krishi Vikas Yojana",
        "benefit": "₹50,000/ha/3yrs for organic farming cluster groups",
        "eligibility": "Farmer clusters of 50+ willing to adopt organic farming",
        "link": "https://pgsindia-ncof.gov.in",
        "emoji": "🌿",
        "applicable_crops": ["rice","wheat","maize","vegetables","pulses"],
        "applicable_states": "all"
    },
    "MIDH": {
        "full_name": "Mission for Integrated Development of Horticulture",
        "benefit": "Subsidy 40-50% for horticulture infrastructure",
        "eligibility": "Farmers growing fruits, vegetables, spices, mushrooms",
        "link": "https://midh.gov.in",
        "emoji": "🍎",
        "applicable_crops": ["tomato","banana","mango","onion","potato","chilli","turmeric","ginger","coconut","garlic"],
        "applicable_states": "all"
    },
    "NMSA": {
        "full_name": "National Mission for Sustainable Agriculture",
        "benefit": "Support for drip/sprinkler irrigation, soil health management",
        "eligibility": "Farmers in water-stressed districts",
        "link": "https://nmsa.dac.gov.in",
        "emoji": "💧",
        "applicable_crops": "all",
        "applicable_drought": ["High", "Medium"]
    },
    "e-NAM": {
        "full_name": "National Agriculture Market",
        "benefit": "Online trading platform — better price discovery, no middlemen",
        "eligibility": "All farmers with produce to sell",
        "link": "https://enam.gov.in",
        "emoji": "🏪",
        "applicable_crops": "all",
        "applicable_states": "all"
    },
    "RKVY": {
        "full_name": "Rashtriya Krishi Vikas Yojana",
        "benefit": "State-level agricultural development projects, infra support",
        "eligibility": "Farmers in participating states",
        "link": "https://rkvy.nic.in",
        "emoji": "🏗️",
        "applicable_crops": "all",
        "applicable_states": "all"
    },
    "Soil Health Card": {
        "full_name": "Soil Health Card Scheme",
        "benefit": "Free soil testing + customized fertilizer recommendations",
        "eligibility": "All farmers",
        "link": "https://soilhealth.dac.gov.in",
        "emoji": "🌱",
        "applicable_crops": "all",
        "applicable_states": "all"
    },
    "PMKSY": {
        "full_name": "Pradhan Mantri Krishi Sinchayee Yojana",
        "benefit": "Har Khet Ko Paani — irrigation connectivity for all farms",
        "eligibility": "Farmers lacking reliable irrigation access",
        "link": "https://pmksy.gov.in",
        "emoji": "🚿",
        "applicable_crops": "all",
        "applicable_states": "all"
    },
    "KCC": {
        "full_name": "Kisan Credit Card",
        "benefit": "Low interest (4-7%) crop loans up to ₹3 lakh",
        "eligibility": "All farmers, fishermen, and animal husbandry workers",
        "link": "https://www.nabard.org/content1.aspx?id=580",
        "emoji": "💳",
        "applicable_crops": "all",
        "applicable_states": "all"
    }
}

# ── Price Trend Multipliers by Month ─────────────────────────
SEASONAL_PRICE_TREND = {
    "rice":    [0.95,0.95,0.97,1.00,1.02,1.05,1.08,1.10,1.05,0.95,0.90,0.93],
    "wheat":   [1.05,1.05,1.00,0.95,0.93,0.95,0.98,1.00,1.02,1.05,1.08,1.07],
    "tomato":  [1.20,1.15,1.00,0.85,0.80,1.10,1.30,1.25,1.10,0.90,0.85,1.00],
    "onion":   [1.30,1.20,1.00,0.85,0.80,0.90,1.10,1.20,1.15,1.00,0.90,1.10],
    "potato":  [1.00,1.00,0.95,0.90,0.90,0.95,1.00,1.05,1.08,1.10,1.05,1.02],
    "maize":   [0.98,0.97,0.98,1.00,1.02,1.05,1.08,1.05,0.98,0.95,0.95,0.97],
    "default": [1.00,1.00,1.00,1.00,1.00,1.02,1.05,1.05,1.02,1.00,0.98,0.98]
}

def get_rain(state):
    return RAIN.get(state.title(), 1000)

def predict_row(model, feat_cols, values):
    return model.predict(np.array([values], dtype=float))

def predict_proba_row(model, feat_cols, values):
    return model.predict_proba(np.array([values], dtype=float))


# ══════════════════════════════════════════════════════════════
@app.route("/")
def home():
    return jsonify({"app":"AgroSentinel India","status":"running","version":"4.0"})

@app.route("/api/crops")
def crops():
    return jsonify({"crops": meta["crops"]})

@app.route("/api/states")
def states():
    return jsonify({"states": meta["states"]})

@app.route("/api/stats")
def stats():
    return jsonify(meta["stats"])

@app.route("/api/emojis")
def emojis():
    return jsonify(CROP_EMOJIS)


# ── Predict All ───────────────────────────────────────────────
@app.route("/api/predict-all", methods=["POST"])
def predict_all():
    d = request.json
    try:
        state    = d.get("state","Maharashtra")
        crop     = d.get("crop","Rice")
        season   = d.get("season","Kharif")
        year     = int(d.get("year", datetime.now().year))
        rainfall = float(d.get("rainfall", get_rain(state)))

        se = safe_enc(le_state,  state.title())
        ce = safe_enc(le_crop,   crop.title())
        ne = safe_enc(le_season, season.strip())

        # ── YIELD ──
        yv   = [se, ce, ne, year, rainfall]
        py   = float(predict_row(yield_model, YIELD_FEAT, yv)[0])
        py   = max(0.01, round(py, 3))
        if py >= 3.0:    yg,yc = "Excellent","success"
        elif py >= 1.5:  yg,yc = "Good",     "info"
        elif py >= 0.8:  yg,yc = "Average",  "warning"
        else:            yg,yc = "Poor",      "danger"

        # ── DROUGHT ──
        dv      = [se, ce, ne, year, rainfall]
        de      = int(predict_row(drought_model, DROUGHT_FEAT, dv)[0])
        drisk   = le_drought.inverse_transform([de])[0]
        dproba  = predict_proba_row(drought_model, DROUGHT_FEAT, dv)[0]
        dconf   = round(float(np.max(dproba))*100, 1)
        dc      = {"High":"danger","Medium":"warning","Low":"success"}.get(drisk,"secondary")
        dadv    = {
            "High":   "🚨 Critically low rainfall — use drought-resistant varieties + drip irrigation.",
            "Medium": "⚠️ Below-average rainfall — monitor reserves + plan supplemental irrigation.",
            "Low":    "✅ Adequate rainfall — standard farming practices are sufficient.",
        }.get(drisk,"")

        # ── FAILURE ──
        fv      = [se, ce, ne, year, rainfall, py]
        fp      = predict_proba_row(failure_model, FAILURE_FEAT, fv)[0]
        fpct    = round(float(fp[1])*100, 1)
        if fpct >= 60:   fr,fc = "High Risk",   "danger"
        elif fpct >= 35: fr,fc = "Medium Risk", "warning"
        else:            fr,fc = "Low Risk",    "success"

        # ── SEASON ──
        sv      = [se, ce, rainfall, year]
        senc    = int(predict_row(season_model, SEASON_FEAT, sv)[0])
        bsea    = le_season.inverse_transform([senc])[0]
        sproba  = predict_proba_row(season_model, SEASON_FEAT, sv)[0]
        sconf   = round(float(np.max(sproba))*100, 1)
        allsea  = {
            le_season.inverse_transform([i])[0]: round(float(p)*100,1)
            for i,p in enumerate(sproba)
        }
        allsea  = dict(sorted(allsea.items(), key=lambda x:x[1], reverse=True))

        emoji   = CROP_EMOJIS.get(crop.title(), CROP_EMOJIS["default"])

        # ── SOIL HEALTH SCORE ──
        soil_score, soil_grade, soil_detail = compute_soil_health(state, rainfall, drisk, py)

        # ── AI ADVISORY ──
        advisory = generate_ai_advisory(
            crop=crop, state=state, season=season, year=year,
            rainfall=rainfall, yield_val=py, yield_grade=yg,
            drought_risk=drisk, failure_risk=fr, failure_pct=fpct,
            best_season=bsea, soil_score=soil_score
        )

        return jsonify({
            "input":   {"state":state.title(),"crop":crop.title(),
                        "season":season,"year":year,"rainfall":rainfall},
            "emoji":   emoji,
            "yield":   {"value":py,"per_acre":round(py*0.4047,3),
                        "unit":"t/ha","grade":yg,"color":yc},
            "drought": {"risk":drisk,"confidence":dconf,"color":dc,"advice":dadv},
            "failure": {"risk":fr,"probability":fpct,"color":fc},
            "season":  {"best":bsea,"confidence":sconf,"all":allsea},
            "soil":    {"score":soil_score,"grade":soil_grade,"detail":soil_detail},
            "advisory": advisory,
            "summary": f"{crop.title()} in {state.title()} — {py} t/ha | Drought: {drisk} | Failure: {fr}",
        })
    except Exception as e:
        return jsonify({"error":str(e)}), 400


# ── NEW: Soil Health Score ─────────────────────────────────────
def compute_soil_health(state, rainfall, drought_risk, yield_val):
    """
    Heuristic soil health score (0-100) based on rainfall, drought risk,
    state agro-zone data and yield performance.
    """
    score = 50  # base

    # Rainfall component (ideal: 800-1500mm)
    if 800 <= rainfall <= 1500:
        score += 20
    elif 600 <= rainfall < 800 or 1500 < rainfall <= 2000:
        score += 12
    elif rainfall < 600:
        score -= 10
    else:
        score += 5  # very high rainfall — leaching risk

    # Drought risk
    if drought_risk == "Low":    score += 15
    elif drought_risk == "Medium": score += 5
    else: score -= 10

    # Yield performance
    if yield_val >= 3.0:   score += 15
    elif yield_val >= 1.5: score += 8
    elif yield_val < 0.8:  score -= 8

    # State soil quality bonus (based on known agro-zones)
    HIGH_SOIL_STATES = ["punjab","haryana","uttar pradesh","west bengal","andhra pradesh","telangana"]
    LOW_SOIL_STATES  = ["rajasthan","gujarat","himachal pradesh","uttarakhand"]
    sl = state.lower()
    if any(s in sl for s in HIGH_SOIL_STATES): score += 10
    elif any(s in sl for s in LOW_SOIL_STATES): score -= 5

    score = max(5, min(100, score))

    if score >= 80:   grade, detail = "Excellent 🟢", "Soil is fertile, well-structured and nutrient-rich. Ideal for high-yield farming."
    elif score >= 65: grade, detail = "Good 🟡", "Soil conditions are favourable. Moderate organic matter. Regular NPK application recommended."
    elif score >= 50: grade, detail = "Moderate 🟠", "Soil shows signs of stress. Improve with compost, green manure and balanced irrigation."
    elif score >= 35: grade, detail = "Poor 🔴", "Soil health is degraded. Urgent need for soil amendment, mulching and moisture conservation."
    else:             grade, detail = "Critical ⚫", "Severe soil degradation detected. Consult local Krishi Vigyan Kendra immediately."

    return score, grade, detail


# ── NEW: AI Advisory Generator ────────────────────────────────
def generate_ai_advisory(crop, state, season, year, rainfall, yield_val,
                          yield_grade, drought_risk, failure_risk, failure_pct,
                          best_season, soil_score):
    """
    Generates a structured rule-based AI advisory paragraph
    explaining WHY the current output is what it is,
    what to improve, and a future prediction.
    """
    crop_t  = crop.title()
    state_t = state.title()

    # WHY section
    why_parts = []
    if drought_risk == "High":
        why_parts.append(f"rainfall of {rainfall}mm is critically below the optimal requirement for {crop_t}")
    elif drought_risk == "Medium":
        why_parts.append(f"rainfall of {rainfall}mm is slightly below optimal, creating moderate water stress")
    else:
        why_parts.append(f"rainfall of {rainfall}mm is adequate for {crop_t} cultivation")

    if season != best_season:
        why_parts.append(f"the selected season ({season}) is not the most optimal — {best_season} shows better historical performance")
    else:
        why_parts.append(f"{season} is the ideal season for {crop_t} in this region")

    why_text = f"📊 **Why this result?** The predicted yield of {yield_val} t/ha ({yield_grade} grade) is primarily because {' and '.join(why_parts)}. " \
               f"Soil health score of {soil_score}/100 also contributes to this outcome in {state_t}."

    # IMPROVE section
    improve_parts = []
    if drought_risk in ["High","Medium"]:
        improve_parts.append("install drip or sprinkler irrigation to reduce water dependence")
    if yield_grade in ["Poor","Average"]:
        improve_parts.append("apply balanced NPK fertilizers (recommended ratio 4:2:1) and organic compost")
        improve_parts.append("use certified high-yielding variety (HYV) seeds from state agriculture department")
    if failure_pct > 35:
        improve_parts.append("diversify with intercropping to reduce total crop failure risk")
    if soil_score < 65:
        improve_parts.append("get a free Soil Health Card test from your nearest Krishi Vigyan Kendra")
    if season != best_season:
        improve_parts.append(f"consider switching to {best_season} season for 15-25% better yield")

    if not improve_parts:
        improve_parts.append("maintain current practices and monitor weather forecasts weekly")

    improve_text = f"💡 **What to improve:** {'; '.join(improve_parts[:3]).capitalize()}."

    # FUTURE PREDICTION
    trend = "stable"
    future_yield = yield_val
    if year < 2026:
        if drought_risk == "Low" and yield_grade in ["Good","Excellent"]:
            trend = "improving"
            future_yield = round(yield_val * 1.12, 2)
        elif drought_risk == "High" or yield_grade == "Poor":
            trend = "declining"
            future_yield = round(yield_val * 0.88, 2)
        else:
            future_yield = round(yield_val * 1.04, 2)

    future_text = (
        f"🔮 **Future outlook (next season):** Based on current trends, {crop_t} yield in {state_t} "
        f"is expected to be {trend}, with a projected yield of approximately {future_yield} t/ha. "
        f"{'Climate variability and water availability remain key risk factors.' if drought_risk != 'Low' else 'Continue with current best practices for sustained performance.'}"
    )

    return {
        "why":     why_text,
        "improve": improve_text,
        "future":  future_text,
        "full":    f"{why_text}\n\n{improve_text}\n\n{future_text}"
    }


# ── NEW: Irrigation Water Requirement Calculator ──────────────
@app.route("/api/irrigation", methods=["POST"])
def irrigation_calculator():
    """
    Calculates irrigation water requirement based on crop, season,
    state rainfall, and farm area.
    """
    d = request.json
    try:
        crop     = d.get("crop","Rice").lower()
        season   = d.get("season","Kharif")
        state    = d.get("state","Maharashtra")
        area_ha  = float(d.get("area_ha", 1.0))
        rainfall = float(d.get("rainfall", get_rain(state)))

        # Get crop water requirement
        crop_data  = CROP_WATER_REQ.get(crop, CROP_WATER_REQ["default"])
        water_need = crop_data.get(season, crop_data.get("default", 600))

        # Effective rainfall (approx 70% of rainfall is usable)
        eff_rain   = min(rainfall * 0.70, water_need)
        irrigation = max(0, water_need - eff_rain)

        # Volume calculations
        volume_liters     = round(irrigation * area_ha * 10000, 0)  # mm * ha -> liters
        volume_m3         = round(volume_liters / 1000, 1)
        daily_requirement = round(irrigation / 120, 1)  # spread over ~120 day season

        # Method recommendation
        if irrigation > 600:
            method = "Drip Irrigation (most efficient — saves 40-60% water)"
            method_emoji = "💧"
            efficiency = "High water stress zone — pressurised irrigation essential"
        elif irrigation > 300:
            method = "Sprinkler Irrigation (recommended for medium water crops)"
            method_emoji = "🌊"
            efficiency = "Moderate irrigation need — sprinkler saves 30% vs flood"
        elif irrigation > 100:
            method = "Furrow / Border Irrigation (suitable for low-need crops)"
            method_emoji = "🌿"
            efficiency = "Low supplemental irrigation — rain-fed with backup"
        else:
            method = "Rain-fed (no supplemental irrigation needed)"
            method_emoji = "🌧️"
            efficiency = "Rainfall is sufficient — natural farming possible"

        # Cost estimate (approx ₹8 per 1000 liters for canal/borewell)
        cost_estimate = round(volume_liters / 1000 * 8, 0)

        return jsonify({
            "crop": crop.title(),
            "season": season,
            "state": state.title(),
            "area_ha": area_ha,
            "rainfall_mm": rainfall,
            "total_water_need_mm": water_need,
            "effective_rainfall_mm": round(eff_rain, 1),
            "irrigation_required_mm": round(irrigation, 1),
            "volume_liters": volume_liters,
            "volume_m3": volume_m3,
            "daily_mm": daily_requirement,
            "recommended_method": method,
            "method_emoji": method_emoji,
            "efficiency_note": efficiency,
            "estimated_cost_inr": cost_estimate,
            "schedule": {
                "morning": f"{round(daily_requirement * 0.6, 1)}mm",
                "evening": f"{round(daily_requirement * 0.4, 1)}mm",
                "frequency": "Daily" if daily_requirement > 5 else "Every 2-3 days"
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ── NEW: Pest & Disease Risk Predictor ───────────────────────
@app.route("/api/pest-risk", methods=["POST"])
def pest_risk():
    """
    Predicts pest and disease risk based on crop, weather conditions,
    and season using rule-based expert system.
    """
    d = request.json
    try:
        crop        = d.get("crop","Rice").lower()
        temperature = float(d.get("temperature", 28))
        humidity    = float(d.get("humidity", 65))
        rainfall    = float(d.get("rainfall", 1000))
        season      = d.get("season","Kharif")
        state       = d.get("state","Maharashtra")

        crop_data = PEST_RISK_DATA.get(crop, PEST_RISK_DATA["default"])

        # Determine weather conditions
        conditions = []
        if humidity > 75:    conditions.append("high_humidity")
        if humidity < 40:    conditions.append("low_humidity")
        if temperature > 32: conditions.append("warm_temp")
        if temperature > 35: conditions.append("hot_dry")
        if temperature < 18: conditions.append("cool_moist")
        if rainfall > 150:   conditions.append("standing_water")
        if rainfall < 30:    conditions.append("dry_weather")

        # Score pests
        pest_results = []
        for pest in crop_data["pests"]:
            matching = sum(1 for rf in pest["risk_factors"] if rf in conditions)
            base_risk = {"High":70,"Medium":45,"Low":25}.get(pest["severity"],45)
            score = min(95, base_risk + matching * 12)
            pest_results.append({
                "name": pest["name"],
                "risk_score": score,
                "risk_level": "High" if score>=65 else "Medium" if score>=40 else "Low",
                "severity": pest["severity"],
                "color": "danger" if score>=65 else "warning" if score>=40 else "success"
            })

        # Score diseases
        disease_results = []
        for disease in crop_data["diseases"]:
            matching = sum(1 for rf in disease["risk_factors"] if rf in conditions)
            base_risk = {"High":65,"Medium":40,"Low":20}.get(disease["severity"],40)
            score = min(95, base_risk + matching * 13)
            disease_results.append({
                "name": disease["name"],
                "risk_score": score,
                "risk_level": "High" if score>=65 else "Medium" if score>=40 else "Low",
                "severity": disease["severity"],
                "color": "danger" if score>=65 else "warning" if score>=40 else "success"
            })

        # Sort by risk
        pest_results.sort(key=lambda x: x["risk_score"], reverse=True)
        disease_results.sort(key=lambda x: x["risk_score"], reverse=True)

        # Overall risk
        all_scores = [p["risk_score"] for p in pest_results] + [d["risk_score"] for d in disease_results]
        overall = round(sum(all_scores)/len(all_scores), 1) if all_scores else 30
        overall_level = "High" if overall >= 60 else "Medium" if overall >= 40 else "Low"
        overall_color = "danger" if overall >= 60 else "warning" if overall >= 40 else "success"

        # Preventive measures
        prevention = []
        if overall >= 60:
            prevention = [
                "Apply recommended pesticides/fungicides immediately",
                "Consult local agriculture officer for spray schedule",
                "Remove and destroy infected plant material",
                "Ensure proper field drainage"
            ]
        elif overall >= 40:
            prevention = [
                "Monitor fields daily for early signs",
                "Apply neem-based organic pesticide as preventive measure",
                "Maintain optimal plant spacing for air circulation",
                "Use yellow sticky traps for pest monitoring"
            ]
        else:
            prevention = [
                "Continue routine field monitoring",
                "Maintain balanced fertilization",
                "Practice crop rotation next season"
            ]

        return jsonify({
            "crop": crop.title(),
            "state": state.title(),
            "season": season,
            "weather_conditions": {
                "temperature": temperature,
                "humidity": humidity,
                "rainfall_annual": rainfall
            },
            "detected_conditions": conditions,
            "pests": pest_results,
            "diseases": disease_results,
            "overall_risk_score": overall,
            "overall_risk_level": overall_level,
            "overall_color": overall_color,
            "prevention_measures": prevention
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ── NEW: Crop Price Forecast (Next 3 Months) ─────────────────
@app.route("/api/price-forecast/<crop_name>")
def price_forecast(crop_name):
    """
    Generates a 3-month price forecast based on current MSP/market price
    and seasonal trend multipliers.
    """
    try:
        key  = crop_name.lower().strip()
        base_price = FALLBACK_PRICES.get(key, 2000)

        # Try to get live price first
        try:
            from app import market_price
        except:
            pass

        trend_key   = key if key in SEASONAL_PRICE_TREND else "default"
        trend_data  = SEASONAL_PRICE_TREND[trend_key]
        current_month = datetime.now().month - 1  # 0-indexed

        months = []
        month_names = ["Jan","Feb","Mar","Apr","May","Jun",
                       "Jul","Aug","Sep","Oct","Nov","Dec"]

        for i in range(3):
            m_idx   = (current_month + i + 1) % 12
            mult    = trend_data[m_idx]
            price   = round(base_price * mult)
            trend   = "↑ Rising" if mult > trend_data[current_month] else \
                      "↓ Falling" if mult < trend_data[current_month] else "→ Stable"
            change_pct = round((mult - trend_data[current_month]) / trend_data[current_month] * 100, 1)

            months.append({
                "month": month_names[m_idx],
                "price": price,
                "trend": trend,
                "change_pct": change_pct,
                "multiplier": round(mult, 3),
                "recommendation": "Good time to sell" if mult > 1.05 else
                                  "Hold stock if possible" if mult > 0.98 else
                                  "Sell quickly — price may drop further"
            })

        # Trading recommendation
        best_month = max(months, key=lambda x: x["price"])
        worst_month = min(months, key=lambda x: x["price"])

        return jsonify({
            "crop": crop_name.title(),
            "current_price": base_price,
            "current_month": month_names[current_month],
            "forecast": months,
            "best_selling_month": best_month["month"],
            "best_selling_price": best_month["price"],
            "worst_month": worst_month["month"],
            "summary": f"Best time to sell {crop_name.title()} is {best_month['month']} "
                       f"at estimated ₹{best_month['price']}/quintal "
                       f"(+{round((best_month['price']-base_price)/base_price*100,1)}% from today)",
            "unit": "₹/quintal",
            "disclaimer": "Price forecasts are indicative based on historical seasonal patterns. Actual market prices may vary."
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ── NEW: Government Scheme Recommender ───────────────────────
@app.route("/api/schemes", methods=["POST"])
def scheme_recommender():
    """
    Recommends applicable government schemes based on crop,
    state, drought risk, and farmer profile.
    """
    d = request.json
    try:
        crop         = d.get("crop","Rice").lower()
        state        = d.get("state","Maharashtra").lower()
        drought_risk = d.get("drought_risk","Low")
        yield_grade  = d.get("yield_grade","Good")
        area_ha      = float(d.get("area_ha", 1.0))

        recommended = []

        for scheme_id, scheme in GOVT_SCHEMES.items():
            include = True

            # Check crop applicability
            if scheme["applicable_crops"] != "all":
                crop_match = any(c in crop for c in scheme["applicable_crops"])
                if not crop_match:
                    include = False

            # Check drought-specific schemes
            if "applicable_drought" in scheme:
                if drought_risk not in scheme["applicable_drought"]:
                    include = False

            if include:
                # Compute relevance score
                relevance = 50
                if scheme_id == "PM-KISAN":
                    if area_ha <= 2: relevance = 95
                    else: relevance = 70
                elif scheme_id == "PMFBY":
                    if drought_risk in ["High","Medium"]: relevance = 90
                    if yield_grade in ["Poor","Average"]: relevance += 5
                elif scheme_id == "NMSA":
                    if drought_risk == "High": relevance = 92
                    elif drought_risk == "Medium": relevance = 75
                elif scheme_id == "MIDH":
                    relevance = 85 if crop in ["tomato","banana","mango","onion","potato","chilli","turmeric","ginger"] else 40
                elif scheme_id == "KCC":
                    relevance = 88
                elif scheme_id == "Soil Health Card":
                    relevance = 80 if yield_grade in ["Poor","Average"] else 65
                elif scheme_id == "PKVY":
                    relevance = 70
                elif scheme_id == "e-NAM":
                    relevance = 75
                elif scheme_id == "PMKSY":
                    if drought_risk in ["High","Medium"]: relevance = 90
                    else: relevance = 60
                elif scheme_id == "RKVY":
                    relevance = 62

                recommended.append({
                    "id": scheme_id,
                    "full_name": scheme["full_name"],
                    "benefit": scheme["benefit"],
                    "eligibility": scheme["eligibility"],
                    "link": scheme["link"],
                    "emoji": scheme["emoji"],
                    "relevance_score": relevance
                })

        # Sort by relevance
        recommended.sort(key=lambda x: x["relevance_score"], reverse=True)

        return jsonify({
            "crop": crop.title(),
            "state": state.title(),
            "total_schemes": len(recommended),
            "schemes": recommended,
            "top_scheme": recommended[0] if recommended else None,
            "message": f"Found {len(recommended)} government schemes applicable for {crop.title()} farming in {state.title()}"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ── Individual endpoints (existing) ──────────────────────────
@app.route("/api/predict-yield", methods=["POST"])
def predict_yield():
    d = request.json
    try:
        state    = d.get("state","")
        crop     = d.get("crop","")
        season   = d.get("season","Kharif")
        year     = int(d.get("year", datetime.now().year))
        rainfall = float(d.get("rainfall", get_rain(state)))
        se = safe_enc(le_state,  state.title())
        ce = safe_enc(le_crop,   crop.title())
        ne = safe_enc(le_season, season.strip())
        py = float(predict_row(yield_model, YIELD_FEAT, [se,ce,ne,year,rainfall])[0])
        py = max(0.01, round(py,3))
        if py>=3.0:   g,c="Excellent","success"
        elif py>=1.5: g,c="Good","info"
        elif py>=0.8: g,c="Average","warning"
        else:         g,c="Poor","danger"
        return jsonify({"crop":crop.title(),"state":state.title(),
            "predicted_yield":py,"yield_per_acre":round(py*0.4047,3),
            "unit":"t/ha","grade":g,"color":c,"rainfall":rainfall})
    except Exception as e:
        return jsonify({"error":str(e)}), 400


@app.route("/api/predict-drought", methods=["POST"])
def predict_drought():
    d = request.json
    try:
        state    = d.get("state","")
        crop     = d.get("crop","")
        season   = d.get("season","Kharif")
        year     = int(d.get("year", datetime.now().year))
        rainfall = float(d.get("rainfall", get_rain(state)))
        se = safe_enc(le_state, state.title())
        ce = safe_enc(le_crop, crop.title())
        ne = safe_enc(le_season, season.strip())
        de = int(predict_row(drought_model, DROUGHT_FEAT, [se,ce,ne,year,rainfall])[0])
        risk   = le_drought.inverse_transform([de])[0]
        proba  = predict_proba_row(drought_model, DROUGHT_FEAT, [se,ce,ne,year,rainfall])[0]
        conf   = round(float(np.max(proba))*100,1)
        color  = {"High":"danger","Medium":"warning","Low":"success"}.get(risk,"secondary")
        return jsonify({"state":state.title(),"crop":crop.title(),
            "drought_risk":risk,"confidence":conf,"color":color,"rainfall":rainfall})
    except Exception as e:
        return jsonify({"error":str(e)}), 400


@app.route("/api/predict-failure", methods=["POST"])
def predict_failure():
    d = request.json
    try:
        state     = d.get("state","")
        crop      = d.get("crop","")
        season    = d.get("season","Kharif")
        year      = int(d.get("year", datetime.now().year))
        rainfall  = float(d.get("rainfall", get_rain(state)))
        yield_val = float(d.get("yield_val", 1.5))
        se = safe_enc(le_state, state.title())
        ce = safe_enc(le_crop, crop.title())
        ne = safe_enc(le_season, season.strip())
        fp = predict_proba_row(failure_model, FAILURE_FEAT,
                               [se,ce,ne,year,rainfall,yield_val])[0]
        pct = round(float(fp[1])*100,1)
        if pct>=60:   r,c="High Risk","danger"
        elif pct>=35: r,c="Medium Risk","warning"
        else:         r,c="Low Risk","success"
        return jsonify({"state":state.title(),"crop":crop.title(),
            "failure_risk":r,"probability":pct,"color":c})
    except Exception as e:
        return jsonify({"error":str(e)}), 400


@app.route("/api/predict-season", methods=["POST"])
def predict_season():
    d = request.json
    try:
        state    = d.get("state","")
        crop     = d.get("crop","")
        year     = int(d.get("year", datetime.now().year))
        rainfall = float(d.get("rainfall", get_rain(state)))
        se = safe_enc(le_state, state.title())
        ce = safe_enc(le_crop, crop.title())
        senc   = int(predict_row(season_model, SEASON_FEAT, [se,ce,rainfall,year])[0])
        season = le_season.inverse_transform([senc])[0]
        proba  = predict_proba_row(season_model, SEASON_FEAT, [se,ce,rainfall,year])[0]
        conf   = round(float(np.max(proba))*100,1)
        allsea = {le_season.inverse_transform([i])[0]:round(float(p)*100,1)
                  for i,p in enumerate(proba)}
        allsea = dict(sorted(allsea.items(),key=lambda x:x[1],reverse=True))
        return jsonify({"state":state.title(),"crop":crop.title(),
            "best_season":season,"confidence":conf,"all_seasons":allsea})
    except Exception as e:
        return jsonify({"error":str(e)}), 400


# ── Weather ───────────────────────────────────────────────────
@app.route("/api/weather/<state_name>")
def weather(state_name):
    coords = STATE_COORDS.get(state_name.lower(), STATE_COORDS["default"])
    lat,lon = coords
    try:
        url = (f"https://api.open-meteo.com/v1/forecast"
               f"?latitude={lat}&longitude={lon}"
               f"&current=temperature_2m,relative_humidity_2m,"
               f"precipitation,wind_speed_10m&timezone=Asia/Kolkata")
        curr = requests.get(url, timeout=6).json().get("current",{})
        return jsonify({
            "state":state_name.title(),
            "temperature":curr.get("temperature_2m",28),
            "humidity":curr.get("relative_humidity_2m",65),
            "precipitation":curr.get("precipitation",0),
            "wind_speed":curr.get("wind_speed_10m",12),
            "source":"Open-Meteo (live)",
        })
    except:
        return jsonify({"state":state_name.title(),
            "temperature":28,"humidity":65,"precipitation":0,
            "wind_speed":12,"source":"Default"})


# ── Market Price ──────────────────────────────────────────────
@app.route("/api/market-price/<crop_name>")
def market_price(crop_name):
    key  = crop_name.lower().strip()
    fb   = FALLBACK_PRICES.get(key, 2000)
    mmap = {"rice":"Rice","wheat":"Wheat","maize":"Maize","tomato":"Tomato",
            "potato":"Potato","onion":"Onion","cotton":"Cotton","soybean":"Soybean",
            "groundnut":"Groundnut","mustard":"Mustard","chickpea":"Gram",
            "arhar":"Arhar/Tur","moong":"Moong","urad":"Black Gram"}
    API  = "579b464db66ec23bdd000001cdd3946e44ce4aad7209ff7b23ac571b"
    mn   = mmap.get(key, crop_name.title())
    try:
        url = (f"https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
               f"?api-key={API}&format=json&limit=5&filters[commodity]={mn}")
        recs = requests.get(url, timeout=7).json().get("records",[])
        px   = [float(r.get("modal_price",0)) for r in recs
                if float(r.get("modal_price",0))>0]
        if px:
            return jsonify({"crop":crop_name.title(),"price":round(sum(px)/len(px)),
                "unit":"₹/quintal","market":recs[0].get("market","India"),
                "state":recs[0].get("state",""),
                "date":recs[0].get("arrival_date",datetime.now().strftime("%d/%m/%Y")),
                "source":"Live — Agmarknet","is_live":True})
    except: pass
    return jsonify({"crop":crop_name.title(),"price":fb,"unit":"₹/quintal",
        "market":"National MSP","state":"India",
        "date":datetime.now().strftime("%d/%m/%Y"),
        "source":"Estimated MSP","is_live":False})


# ── Retrain ───────────────────────────────────────────────────
@app.route("/api/retrain", methods=["POST"])
def retrain():
    global retrain_status
    if retrain_status["status"] == "running":
        return jsonify({"message":"Already running"}), 400
    def run():
        global retrain_status,yield_model,drought_model,failure_model,season_model
        global le_state,le_crop,le_season,le_drought,feat_names,meta
        retrain_status = {"status":"running","message":"Training..."}
        try:
            script = os.path.join(BASE_DIR,"ml_models","train_model.py")
            res    = subprocess.run([sys.executable,script],
                                    capture_output=True,text=True,timeout=300)
            if res.returncode == 0:
                yield_model   = joblib.load(os.path.join(MODEL_DIR,"yield_model.pkl"))
                drought_model = joblib.load(os.path.join(MODEL_DIR,"drought_model.pkl"))
                failure_model = joblib.load(os.path.join(MODEL_DIR,"failure_model.pkl"))
                season_model  = joblib.load(os.path.join(MODEL_DIR,"season_model.pkl"))
                le_state      = joblib.load(os.path.join(MODEL_DIR,"le_state.pkl"))
                le_crop       = joblib.load(os.path.join(MODEL_DIR,"le_crop.pkl"))
                le_season     = joblib.load(os.path.join(MODEL_DIR,"le_season.pkl"))
                le_drought    = joblib.load(os.path.join(MODEL_DIR,"le_drought.pkl"))
                feat_names    = joblib.load(os.path.join(MODEL_DIR,"feature_names.pkl"))
                meta          = joblib.load(os.path.join(MODEL_DIR,"metadata.pkl"))
                retrain_status = {"status":"success","message":"All models retrained!"}
            else:
                retrain_status = {"status":"error","message":res.stderr[:200]}
        except Exception as e:
            retrain_status = {"status":"error","message":str(e)}
    threading.Thread(target=run).start()
    return jsonify({"message":"Retraining started"})

@app.route("/api/retrain-status")
def retrain_status_route():
    return jsonify(retrain_status)


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False, port=5000)