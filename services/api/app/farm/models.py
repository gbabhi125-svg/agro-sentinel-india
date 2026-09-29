"""
Loads the honestly-retrained models from ml/registry/v1 and exposes
prediction functions. Unknown crop/state/season is rejected with a clear
error instead of silently falling back to index 0 (the old safe_enc bug),
which used to produce a confident-looking prediction for the wrong crop.
"""
import json
import os

import joblib

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
REGISTRY_DIR = os.path.join(BASE_DIR, "ml", "registry", "v1")


class UnknownValueError(ValueError):
    def __init__(self, field: str, value: str, valid_sample: list):
        self.field = field
        self.value = value
        super().__init__(
            f"Unknown {field} '{value}'. This model was trained on real APY data and does not "
            f"recognise it — examples of valid values: {valid_sample[:8]}"
        )


class FarmModels:
    def __init__(self):
        self.yield_model = joblib.load(os.path.join(REGISTRY_DIR, "yield_model.pkl"))
        self.failure_model = joblib.load(os.path.join(REGISTRY_DIR, "failure_model.pkl"))
        self.season_model = joblib.load(os.path.join(REGISTRY_DIR, "season_model.pkl"))
        self.le_state = joblib.load(os.path.join(REGISTRY_DIR, "le_state.pkl"))
        self.le_crop = joblib.load(os.path.join(REGISTRY_DIR, "le_crop.pkl"))
        self.le_season = joblib.load(os.path.join(REGISTRY_DIR, "le_season.pkl"))
        with open(os.path.join(REGISTRY_DIR, "metadata.json")) as f:
            self.meta = json.load(f)
        with open(os.path.join(REGISTRY_DIR, "state_lpa.json")) as f:
            self.state_lpa = json.load(f)
        self.feat = self.meta["feature_names"]

    def _enc(self, encoder, field, value):
        try:
            return int(encoder.transform([value])[0])
        except ValueError:
            raise UnknownValueError(field, value, list(encoder.classes_))

    def predict_yield(self, state, crop, season, year, rainfall, fertilizer, pesticide):
        se, ce, ne = (self._enc(self.le_state, "state", state),
                      self._enc(self.le_crop, "crop", crop),
                      self._enc(self.le_season, "season", season))
        x = [[se, ce, ne, year, rainfall, fertilizer, pesticide]]
        value = max(0.0, round(float(self.yield_model.predict(x)[0]), 3))
        unit = "nuts/ha" if crop == "Coconut" else "t/ha"
        per_crop = self.meta["validation"]["yield_test_mae_per_crop"].get(crop)
        return {
            "predicted_yield": value, "unit": unit,
            "crop_median_yield": self.meta["crop_median_yield_tha"].get(crop),
            "model_mae_for_this_crop": per_crop["mae"] if per_crop else None,
            "model_mae_note": ("out-of-time test MAE for this crop, n=%d" % per_crop["n_test"])
            if per_crop else "no out-of-time test rows for this crop — treat with more caution",
        }

    def predict_failure(self, state, crop, season, year, rainfall, fertilizer, pesticide):
        se, ce, ne = (self._enc(self.le_state, "state", state),
                      self._enc(self.le_crop, "crop", crop),
                      self._enc(self.le_season, "season", season))
        x = [[se, ce, ne, year, rainfall, fertilizer, pesticide]]
        proba = float(self.failure_model.predict_proba(x)[0][1])
        v = self.meta["validation"]
        return {
            "failure_probability": round(proba, 3),
            "risk_level": "High" if proba >= 0.5 else "Medium" if proba >= 0.25 else "Low",
            "model_honesty_note": (
                f"Out-of-time test precision={v['failure_test_precision']}, "
                f"recall={v['failure_test_recall']} — this model catches "
                f"{round(v['failure_test_recall']*100)}% of real failures, and "
                f"{round((1-v['failure_test_precision'])*100)}% of its 'failure' warnings are false alarms."
            ),
        }

    def recommend_season(self, state, crop, year, rainfall):
        if crop in self.meta.get("single_season_crops", []):
            return {"suppressed": True, "reason": f"{crop} is grown in only one season historically — "
                                                    "a season-switch recommendation would be meaningless."}
        se, ce = self._enc(self.le_state, "state", state), self._enc(self.le_crop, "crop", crop)
        x = [[se, ce, year, rainfall]]
        pred = int(self.season_model.predict(x)[0])
        proba = self.season_model.predict_proba(x)[0]
        best = self.le_season.inverse_transform([pred])[0]
        all_seasons = {self.le_season.inverse_transform([i])[0]: round(float(p), 3)
                       for i, p in enumerate(proba)}
        return {"suppressed": False, "best_season": best,
                "confidence": round(float(max(proba)), 3), "all_seasons": all_seasons}

    def drought_risk(self, state, rainfall_mm):
        """Rule-based, not ML: % departure of the given rainfall from this state's
        long-period average (LPA), simplified-IMD-style thresholds. See
        ml/training/train.py for why this is a rule and not a trained classifier."""
        lpa = self.state_lpa.get(state, self.state_lpa["_national_mean"])
        departure_pct = round((rainfall_mm - lpa) / lpa * 100, 1)
        if departure_pct >= 20:
            category, risk = "Excess", "Low"
        elif departure_pct >= -19:
            category, risk = "Normal", "Low"
        elif departure_pct >= -59:
            category, risk = "Deficient", "Medium"
        else:
            category, risk = "Scanty", "High"
        return {
            "risk_level": risk, "category": category, "departure_from_lpa_pct": departure_pct,
            "state_lpa_mm": lpa, "given_rainfall_mm": rainfall_mm,
            "method": "rule-based departure from long-period average, not a trained ML model",
        }


_instance: FarmModels | None = None


def get_farm_models() -> FarmModels:
    global _instance
    if _instance is None:
        _instance = FarmModels()
    return _instance
