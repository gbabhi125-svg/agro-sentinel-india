"""
AgroSentinel — honest ML training pipeline.

Fixes, vs. the old ml_models/train_model.py:
  - Drought risk is NOT a trained classifier any more. The old code labelled
    drought_risk from `rainfall` and then fed `rainfall` back in as a
    training feature, so the model just memorised its own label (~100%
    "accuracy"). Drought is now a transparent rule (rainfall departure from
    each state's own long-period average), computed once here and saved as
    a lookup table + threshold function — see drought.py in this folder.
  - Crop failure no longer takes the predicted/actual yield as an input
    feature (the old code did — the label is a threshold on yield, so that
    is direct leakage). It now predicts failure from only what is known
    before harvest: state, crop, season, year, rainfall, fertilizer,
    pesticide use.
  - Evaluation is out-of-time, not a random split. Random splitting let
    near-identical rows from the same year leak between train and test.
    Models here train on 1997-2016 and are scored on 2017-2019, which is
    the actual task a farmer needs: predicting a year the model never saw.
"""
import json
import os
import warnings

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import (
    accuracy_score, confusion_matrix, f1_score, mean_absolute_error,
    precision_score, r2_score, recall_score,
)
from sklearn.preprocessing import LabelEncoder

warnings.filterwarnings("ignore")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATASETS_DIR = os.path.join(BASE_DIR, "datasets")
REGISTRY_DIR = os.path.join(BASE_DIR, "ml", "registry", "v1")
os.makedirs(REGISTRY_DIR, exist_ok=True)

TRAIN_YEARS_MAX = 2016
TEST_YEARS = [2017, 2018, 2019]  # 2020 dropped below (only 37 rows, partial year)

# IMD met-subdivision -> crop_yield.csv state name. Several subdivisions map
# to one state (simple average, no population/area weighting) and a few
# subdivisions (Andaman & Nicobar, Lakshadweep, East/West Rajasthan) have no
# match in crop_yield.csv's state list, so those states fall back to the
# national mean LPA. This is a documented approximation, not ground truth.
SUBDIVISION_TO_STATE = {
    "ARUNACHAL PRADESH": ["Arunachal Pradesh"],
    "ASSAM & MEGHALAYA": ["Assam", "Meghalaya"],
    "BIHAR": ["Bihar"],
    "CHHATTISGARH": ["Chhattisgarh"],
    "COASTAL ANDHRA PRADESH": ["Andhra Pradesh"],
    "RAYALSEEMA": ["Andhra Pradesh"],
    "COASTAL KARNATAKA": ["Karnataka"],
    "NORTH INTERIOR KARNATAKA": ["Karnataka"],
    "SOUTH INTERIOR KARNATAKA": ["Karnataka"],
    "EAST MADHYA PRADESH": ["Madhya Pradesh"],
    "WEST MADHYA PRADESH": ["Madhya Pradesh"],
    "EAST UTTAR PRADESH": ["Uttar Pradesh"],
    "WEST UTTAR PRADESH": ["Uttar Pradesh"],
    "GANGETIC WEST BENGAL": ["West Bengal"],
    "SUB HIMALAYAN WEST BENGAL & SIKKIM": ["West Bengal", "Sikkim"],
    "GUJARAT REGION": ["Gujarat"],
    "SAURASHTRA & KUTCH": ["Gujarat"],
    "HARYANA DELHI & CHANDIGARH": ["Haryana", "Delhi"],
    "HIMACHAL PRADESH": ["Himachal Pradesh"],
    "JAMMU & KASHMIR": ["Jammu and Kashmir"],
    "JHARKHAND": ["Jharkhand"],
    "KERALA": ["Kerala"],
    "KONKAN & GOA": ["Goa"],
    "MADHYA MAHARASHTRA": ["Maharashtra"],
    "MATATHWADA": ["Maharashtra"],
    "VIDARBHA": ["Maharashtra"],
    "NAGA MANI MIZO TRIPURA": ["Nagaland", "Manipur", "Mizoram", "Tripura"],
    "ORISSA": ["Odisha"],
    "PUNJAB": ["Punjab"],
    "TAMIL NADU": ["Tamil Nadu", "Puducherry"],
    "TELANGANA": ["Telangana"],
    "UTTARAKHAND": ["Uttarakhand"],
}


def build_state_lpa():
    """Long-period average annual rainfall per state, from the 1901-2015 series."""
    rain = pd.read_csv(os.path.join(DATASETS_DIR, "rainfall in india 1901-2015.csv"))
    rain.columns = rain.columns.str.strip().str.upper()
    months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
    rain["annual"] = rain[months].sum(axis=1)
    subdiv_lpa = rain.groupby("SUBDIVISION")["annual"].mean()

    state_values = {}
    for subdiv, lpa in subdiv_lpa.items():
        for state in SUBDIVISION_TO_STATE.get(subdiv, []):
            state_values.setdefault(state, []).append(lpa)

    national_mean = float(subdiv_lpa.mean())
    state_lpa = {state: round(float(np.mean(vals)), 1) for state, vals in state_values.items()}
    state_lpa["_national_mean"] = round(national_mean, 1)
    return state_lpa


# Coconut yield is recorded in nuts/ha in this dataset, not tonnes/ha like
# every other crop — a global tonnes-based metric would be meaningless for
# it. It is trained and reported separately for that reason.
NON_TONNE_UNIT_CROPS = {"Coconut": "nuts/ha"}


def load_yield_data():
    df = pd.read_csv(os.path.join(DATASETS_DIR, "crop_yield.csv"))
    df["Crop"] = df["Crop"].str.strip()
    df["Season"] = df["Season"].str.strip()
    df["State"] = df["State"].str.strip()
    df = df.rename(columns={
        "Crop_Year": "year", "Annual_Rainfall": "rainfall",
        "Fertilizer": "fertilizer", "Pesticide": "pesticide", "Yield": "yield_tha",
    })
    df = df[df["year"] <= max(TEST_YEARS)]  # drop the incomplete 2020 partial year

    # Per-crop 99th-percentile cap: a handful of rows have implausible values
    # (e.g. Maize up to 989 t/ha, Potato up to 311 t/ha) that are almost
    # certainly data-entry errors in the source APY dataset, not real yields.
    # Capped per crop, not globally, since a global cutoff would be dominated
    # by Coconut's nuts/ha scale. Rows above the cap are dropped, and the
    # count dropped is reported so this cleaning step is auditable.
    before = len(df)
    caps = df.groupby("Crop")["yield_tha"].transform(lambda s: s.quantile(0.99))
    df = df[df["yield_tha"] <= caps].copy()
    dropped = before - len(df)
    print(f"      Dropped {dropped} rows above each crop's own 99th-percentile "
          f"yield (likely data-entry errors)")
    return df, dropped


def out_of_time_split(df):
    train = df[df["year"] <= TRAIN_YEARS_MAX].copy()
    test = df[df["year"].isin(TEST_YEARS)].copy()
    return train, test


def encode(train, test, col, enc):
    train[col + "_enc"] = enc.fit_transform(train[col])
    known = set(enc.classes_)
    test = test[test[col].isin(known)].copy()
    test[col + "_enc"] = enc.transform(test[col])
    return train, test


def main():
    print("=" * 70)
    print("AgroSentinel — honest training pipeline")
    print("=" * 70)

    state_lpa = build_state_lpa()
    print(f"\n[1/5] Rainfall LPA computed for {len(state_lpa) - 1} states "
          f"(national fallback = {state_lpa['_national_mean']} mm)")

    df, dropped_outlier_rows = load_yield_data()
    train, test = out_of_time_split(df)
    print(f"[2/5] crop_yield.csv: {len(df):,} rows, {df['Crop'].nunique()} crops, "
          f"{df['State'].nunique()} states, years {df['year'].min()}-{df['year'].max()}")
    print(f"      Train (<= {TRAIN_YEARS_MAX}): {len(train):,} rows | "
          f"Test ({TEST_YEARS[0]}-{TEST_YEARS[-1]}, out-of-time): {len(test):,} rows")

    le_state, le_crop, le_season = LabelEncoder(), LabelEncoder(), LabelEncoder()
    train, test = encode(train, test, "State", le_state)
    train, test = encode(train, test, "Crop", le_crop)
    train, test = encode(train, test, "Season", le_season)

    YIELD_FEAT = ["State_enc", "Crop_enc", "Season_enc", "year", "rainfall", "fertilizer", "pesticide"]
    FAILURE_FEAT = YIELD_FEAT  # deliberately excludes yield_tha
    SEASON_FEAT = ["State_enc", "Crop_enc", "year", "rainfall"]

    # ── Yield regression, evaluated out-of-time ──────────────────────────
    print("\n[3/5] Yield regression (RandomForestRegressor)")
    yield_model = RandomForestRegressor(n_estimators=150, max_depth=14, random_state=42, n_jobs=-1)
    yield_model.fit(train[YIELD_FEAT], train["yield_tha"])
    pred = yield_model.predict(test[YIELD_FEAT])
    yield_r2 = r2_score(test["yield_tha"], pred)
    yield_mae = mean_absolute_error(test["yield_tha"], pred)
    print(f"      Test R^2={yield_r2:.3f}  MAE={yield_mae:.3f} t/ha  (out-of-time, {TEST_YEARS})")
    per_year_r2 = {}
    for y in TEST_YEARS:
        mask = test["year"] == y
        if mask.sum() > 5:
            per_year_r2[str(y)] = round(float(r2_score(test.loc[mask, "yield_tha"], pred[mask.values])), 3)
    print(f"      Per-year R^2: {per_year_r2}")

    # Pooled MAE is dominated by whichever crop has the largest yield scale
    # (t/ha ranges from ~0.5 for pulses to ~50+ for sugarcane), so it is
    # reported per crop as well — this is the number that actually tells a
    # farmer growing a specific crop how far off to expect the prediction.
    test = test.assign(_pred=pred)
    per_crop_mae = {}
    for crop, g in test.groupby("Crop"):
        if len(g) >= 5:
            per_crop_mae[crop] = {
                "n_test": int(len(g)),
                "mae": round(float(mean_absolute_error(g["yield_tha"], g["_pred"])), 3),
                "mean_actual": round(float(g["yield_tha"].mean()), 3),
                "unit": NON_TONNE_UNIT_CROPS.get(crop, "t/ha"),
            }
    test = test.drop(columns="_pred")

    # ── Crop failure classification, ex-ante features only ───────────────
    print("\n[4/5] Crop failure classification (RandomForestClassifier)")
    crop_median_train = train.groupby("Crop")["yield_tha"].median()
    global_median_train = train["yield_tha"].median()
    train["failure"] = (train["yield_tha"] < train["Crop"].map(crop_median_train) * 0.60).astype(int)
    test["failure"] = (
        test["yield_tha"] < test["Crop"].map(crop_median_train).fillna(global_median_train) * 0.60
    ).astype(int)

    failure_model = RandomForestClassifier(
        n_estimators=150, max_depth=12, random_state=42, n_jobs=-1, class_weight="balanced"
    )
    failure_model.fit(train[FAILURE_FEAT], train["failure"])
    fpred = failure_model.predict(test[FAILURE_FEAT])
    failure_acc = accuracy_score(test["failure"], fpred)
    failure_precision = precision_score(test["failure"], fpred, zero_division=0)
    failure_recall = recall_score(test["failure"], fpred, zero_division=0)
    failure_f1 = f1_score(test["failure"], fpred, zero_division=0)
    cm = confusion_matrix(test["failure"], fpred).tolist()
    print(f"      Test accuracy={failure_acc:.3f}  precision={failure_precision:.3f}  "
          f"recall={failure_recall:.3f}  f1={failure_f1:.3f}")
    print(f"      Confusion matrix [[TN,FP],[FN,TP]]: {cm}")
    print(f"      Failure rate in test set: {test['failure'].mean() * 100:.1f}% "
          f"(baseline accuracy from always predicting 'no failure' = "
          f"{(1 - test['failure'].mean()) * 100:.1f}%)")

    # ── Season classification ─────────────────────────────────────────
    print("\n[5/5] Historically-typical-season classifier (RandomForestClassifier)")
    season_model = RandomForestClassifier(n_estimators=120, max_depth=10, random_state=42, n_jobs=-1)
    season_model.fit(train[SEASON_FEAT], train["Season_enc"])
    spred = season_model.predict(test[SEASON_FEAT])
    season_acc = accuracy_score(test["Season_enc"], spred)
    # A crop grown in essentially one season historically (>=90% of its records) gets no
    # season-switch advice — a few stray mislabelled rows (e.g. 2 "Kharif" rows out of 172
    # for Coconut, which is really a whole-year perennial) shouldn't count against that.
    season_dominance = train.groupby("Crop")["Season"].agg(lambda s: s.value_counts(normalize=True).iloc[0])
    single_season_crops = sorted(season_dominance[season_dominance >= 0.9].index.tolist())
    print(f"      Test accuracy={season_acc:.3f} "
          f"(high partly because {len(single_season_crops)}/{train['Crop'].nunique()} crops "
          f"are single-season by convention — season-switch advice is suppressed for those)")

    # ── Save artifacts ───────────────────────────────────────────────────
    joblib.dump(yield_model, os.path.join(REGISTRY_DIR, "yield_model.pkl"), compress=3)
    joblib.dump(failure_model, os.path.join(REGISTRY_DIR, "failure_model.pkl"), compress=3)
    joblib.dump(season_model, os.path.join(REGISTRY_DIR, "season_model.pkl"), compress=3)
    joblib.dump(le_state, os.path.join(REGISTRY_DIR, "le_state.pkl"))
    joblib.dump(le_crop, os.path.join(REGISTRY_DIR, "le_crop.pkl"))
    joblib.dump(le_season, os.path.join(REGISTRY_DIR, "le_season.pkl"))

    with open(os.path.join(REGISTRY_DIR, "state_lpa.json"), "w") as f:
        json.dump(state_lpa, f, indent=2)

    metadata = {
        "feature_names": {
            "yield": YIELD_FEAT, "failure": FAILURE_FEAT, "season": SEASON_FEAT,
        },
        "crops": sorted(df["Crop"].unique().tolist()),
        "states": sorted(df["State"].unique().tolist()),
        "seasons": sorted(df["Season"].unique().tolist()),
        "single_season_crops": single_season_crops,
        "crop_median_yield_tha": {k: round(float(v), 3) for k, v in crop_median_train.items()},
        "known_issues": [
            "Coconut yield is in nuts/ha, every other crop is in t/ha — never compare Coconut's "
            "MAE against another crop's.",
            "%d rows were dropped for exceeding their own crop's 99th-percentile yield "
            "(likely data-entry errors in the source APY dataset)." % (dropped_outlier_rows,),
            "Rainfall LPA for states with no matching IMD subdivision "
            "(uses the national mean instead — see drought.py) is a coarser estimate.",
        ],
        "validation": {
            "method": "out-of-time: trained on years <= %d, tested on %s "
                      "(never seen during training)" % (TRAIN_YEARS_MAX, TEST_YEARS),
            "n_train": int(len(train)), "n_test": int(len(test)),
            "yield_test_r2": round(float(yield_r2), 4),
            "yield_test_mae_t_per_ha_pooled": round(float(yield_mae), 4),
            "yield_test_mae_note": "pooled MAE mixes crop scales, see yield_test_mae_per_crop instead",
            "yield_test_mae_per_crop": per_crop_mae,
            "yield_per_year_r2": per_year_r2,
            "failure_test_accuracy": round(float(failure_acc), 4),
            "failure_test_precision": round(float(failure_precision), 4),
            "failure_test_recall": round(float(failure_recall), 4),
            "failure_test_f1": round(float(failure_f1), 4),
            "failure_confusion_matrix": cm,
            "failure_test_base_rate": round(float(test["failure"].mean()), 4),
            "season_test_accuracy": round(float(season_acc), 4),
        },
    }
    with open(os.path.join(REGISTRY_DIR, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\nSaved models + metadata to {REGISTRY_DIR}")
    print("No drought model is saved — drought risk is computed by a rule, see farm/drought.py")


if __name__ == "__main__":
    main()
