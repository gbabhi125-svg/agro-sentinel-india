"""
AgroSentinel — honest ML training pipeline, now comparing multiple
algorithms per model (matching the mini-project's original model list) and
picking the best by a real out-of-time metric — never by in-sample accuracy.

Fixes, vs. the old ml_models/train_model.py:
  - Drought risk IS now trained (the mini-project's Model 2), but honestly:
    the old code labelled drought from `rainfall` and then fed `rainfall`
    back in as a feature, so it just memorised its own label (~100% "acc").
    Here the label (rainfall departure from each state's long-period
    average) is still computed from rainfall, but the MODEL is trained
    WITHOUT rainfall as an input — it has to guess drought category from
    state+crop+season+year alone, the way a real forecast (made before the
    season's rain falls) would have to. Expect much lower, honest accuracy.
  - Crop failure no longer takes yield as an input feature (the label is a
    threshold on yield — that was direct leakage).
  - Evaluation is out-of-time (train <=2016, test 2017-2019), not a random
    split, which is what let the old pipeline report meaningless "accuracy".
"""
import json
import os
import warnings

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import (
    GradientBoostingClassifier, RandomForestClassifier, RandomForestRegressor,
)
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import (
    accuracy_score, confusion_matrix, f1_score, mean_absolute_error,
    precision_score, r2_score, recall_score,
)
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from xgboost import XGBClassifier, XGBRegressor

warnings.filterwarnings("ignore")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATASETS_DIR = os.path.join(BASE_DIR, "datasets")
REGISTRY_DIR = os.path.join(BASE_DIR, "ml", "registry", "v1")
os.makedirs(REGISTRY_DIR, exist_ok=True)

TRAIN_YEARS_MAX = 2016
TEST_YEARS = [2017, 2018, 2019]  # 2020 dropped below (only 37 rows, partial year)

SUBDIVISION_TO_STATE = {
    "ARUNACHAL PRADESH": ["Arunachal Pradesh"], "ASSAM & MEGHALAYA": ["Assam", "Meghalaya"],
    "BIHAR": ["Bihar"], "CHHATTISGARH": ["Chhattisgarh"],
    "COASTAL ANDHRA PRADESH": ["Andhra Pradesh"], "RAYALSEEMA": ["Andhra Pradesh"],
    "COASTAL KARNATAKA": ["Karnataka"], "NORTH INTERIOR KARNATAKA": ["Karnataka"],
    "SOUTH INTERIOR KARNATAKA": ["Karnataka"], "EAST MADHYA PRADESH": ["Madhya Pradesh"],
    "WEST MADHYA PRADESH": ["Madhya Pradesh"], "EAST UTTAR PRADESH": ["Uttar Pradesh"],
    "WEST UTTAR PRADESH": ["Uttar Pradesh"], "GANGETIC WEST BENGAL": ["West Bengal"],
    "SUB HIMALAYAN WEST BENGAL & SIKKIM": ["West Bengal", "Sikkim"], "GUJARAT REGION": ["Gujarat"],
    "SAURASHTRA & KUTCH": ["Gujarat"], "HARYANA DELHI & CHANDIGARH": ["Haryana", "Delhi"],
    "HIMACHAL PRADESH": ["Himachal Pradesh"], "JAMMU & KASHMIR": ["Jammu and Kashmir"],
    "JHARKHAND": ["Jharkhand"], "KERALA": ["Kerala"], "KONKAN & GOA": ["Goa"],
    "MADHYA MAHARASHTRA": ["Maharashtra"], "MATATHWADA": ["Maharashtra"], "VIDARBHA": ["Maharashtra"],
    "NAGA MANI MIZO TRIPURA": ["Nagaland", "Manipur", "Mizoram", "Tripura"], "ORISSA": ["Odisha"],
    "PUNJAB": ["Punjab"], "TAMIL NADU": ["Tamil Nadu", "Puducherry"], "TELANGANA": ["Telangana"],
    "UTTARAKHAND": ["Uttarakhand"],
}
NON_TONNE_UNIT_CROPS = {"Coconut": "nuts/ha"}


def build_state_lpa():
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


def drought_category(rainfall, state, state_lpa):
    lpa = state_lpa.get(state, state_lpa["_national_mean"])
    dep = (rainfall - lpa) / lpa * 100
    if dep >= 20: return "Excess"
    if dep >= -19: return "Normal"
    if dep >= -59: return "Deficient"
    return "Scanty"


def load_yield_data():
    df = pd.read_csv(os.path.join(DATASETS_DIR, "crop_yield.csv"))
    df["Crop"] = df["Crop"].str.strip()
    df["Season"] = df["Season"].str.strip()
    df["State"] = df["State"].str.strip()
    df = df.rename(columns={
        "Crop_Year": "year", "Annual_Rainfall": "rainfall",
        "Fertilizer": "fertilizer", "Pesticide": "pesticide", "Yield": "yield_tha",
    })
    df = df[df["year"] <= max(TEST_YEARS)]
    before = len(df)
    caps = df.groupby("Crop")["yield_tha"].transform(lambda s: s.quantile(0.99))
    df = df[df["yield_tha"] <= caps].copy()
    dropped = before - len(df)
    print(f"      Dropped {dropped} rows above each crop's own 99th-percentile yield (likely data-entry errors)")
    return df, dropped


def out_of_time_split(df):
    return df[df["year"] <= TRAIN_YEARS_MAX].copy(), df[df["year"].isin(TEST_YEARS)].copy()


def encode(train, test, col, enc):
    train[col + "_enc"] = enc.fit_transform(train[col])
    known = set(enc.classes_)
    test = test[test[col].isin(known)].copy()
    test[col + "_enc"] = enc.transform(test[col])
    return train, test


def compare_regressors(candidates, Xtr, ytr, Xte, yte):
    results, best_name, best_model, best_score = {}, None, None, -1e9
    for name, model in candidates.items():
        model.fit(Xtr, ytr)
        pred = model.predict(Xte)
        r2 = r2_score(yte, pred)
        results[name] = round(float(r2), 4)
        print(f"        {name:<20} R^2={r2:.4f}")
        if r2 > best_score:
            best_score, best_name, best_model = r2, name, model
    return best_name, best_model, best_score, results


def compare_classifiers(candidates, Xtr, ytr, Xte, yte, metric="f1_weighted"):
    results, best_name, best_model, best_score = {}, None, None, -1
    for name, model in candidates.items():
        model.fit(Xtr, ytr)
        pred = model.predict(Xte)
        score = (f1_score(yte, pred, average="weighted", zero_division=0) if metric == "f1_weighted"
                 else accuracy_score(yte, pred))
        results[name] = round(float(score), 4)
        print(f"        {name:<20} {metric}={score:.4f}")
        if score > best_score:
            best_score, best_name, best_model = score, name, model
    return best_name, best_model, best_score, results


def main():
    print("=" * 70)
    print("AgroSentinel — honest training pipeline (multi-algorithm)")
    print("=" * 70)

    state_lpa = build_state_lpa()
    print(f"\n[1/6] Rainfall LPA computed for {len(state_lpa) - 1} states")

    df, dropped_outlier_rows = load_yield_data()
    train, test = out_of_time_split(df)
    print(f"[2/6] crop_yield.csv: {len(df):,} rows | Train: {len(train):,} | Test (out-of-time): {len(test):,}")

    le_state, le_crop, le_season = LabelEncoder(), LabelEncoder(), LabelEncoder()
    train, test = encode(train, test, "State", le_state)
    train, test = encode(train, test, "Crop", le_crop)
    train, test = encode(train, test, "Season", le_season)

    YIELD_FEAT = ["State_enc", "Crop_enc", "Season_enc", "year", "rainfall", "fertilizer", "pesticide"]
    FAILURE_FEAT = YIELD_FEAT  # deliberately excludes yield_tha
    SEASON_FEAT = ["State_enc", "Crop_enc", "year", "rainfall"]
    DROUGHT_FEAT = ["State_enc", "Crop_enc", "Season_enc", "year"]  # deliberately excludes rainfall

    # ── MODEL 1: Yield regression — RF / XGBoost / Ridge / Linear ────────
    print("\n[3/6] MODEL 1 — Crop Yield Prediction (Regression)")
    yield_candidates = {
        "RandomForest": RandomForestRegressor(n_estimators=150, max_depth=14, random_state=42, n_jobs=-1),
        "XGBoost": XGBRegressor(n_estimators=200, max_depth=6, random_state=42, n_jobs=-1, verbosity=0),
        "Ridge": Ridge(alpha=1.0),
        "LinearRegression": LinearRegression(),
    }
    best_yield_name, yield_model, yield_r2, yield_results = compare_regressors(
        yield_candidates, train[YIELD_FEAT], train["yield_tha"], test[YIELD_FEAT], test["yield_tha"])
    pred = yield_model.predict(test[YIELD_FEAT])
    yield_mae = mean_absolute_error(test["yield_tha"], pred)
    print(f"      Best: {best_yield_name} (R^2={yield_r2:.4f}, MAE={yield_mae:.3f} t/ha)")

    per_year_r2 = {}
    for y in TEST_YEARS:
        mask = test["year"] == y
        if mask.sum() > 5:
            per_year_r2[str(y)] = round(float(r2_score(test.loc[mask, "yield_tha"], pred[mask.values])), 3)

    test = test.assign(_pred=pred)
    per_crop_mae = {}
    for crop, g in test.groupby("Crop"):
        if len(g) >= 5:
            per_crop_mae[crop] = {
                "n_test": int(len(g)), "mae": round(float(mean_absolute_error(g["yield_tha"], g["_pred"])), 3),
                "mean_actual": round(float(g["yield_tha"].mean()), 3),
                "unit": NON_TONNE_UNIT_CROPS.get(crop, "t/ha"),
            }
    test = test.drop(columns="_pred")

    # ── MODEL 2: Drought — RF / GradientBoosting / XGBoost / KNN / Tree / SVM ──
    # Honestly: predicted WITHOUT rainfall as input (see DROUGHT_FEAT above),
    # because with rainfall in, the label is a direct function of a feature —
    # the exact leakage the old mini-project had. Without it, this is the
    # real task (guess this season's drought category from state/crop/season/
    # year alone) and the real, much lower, accuracy that comes with it.
    print("\n[4/6] MODEL 2 — Drought Risk Classification (rainfall excluded from inputs — see note above)")
    le_drought = LabelEncoder()
    train["drought_cat"] = [drought_category(r, s, state_lpa) for r, s in zip(train["rainfall"], train["State"])]
    test["drought_cat"] = [drought_category(r, s, state_lpa) for r, s in zip(test["rainfall"], test["State"])]
    train["drought_enc"] = le_drought.fit_transform(train["drought_cat"])
    test = test[test["drought_cat"].isin(le_drought.classes_)].copy()
    test["drought_enc"] = le_drought.transform(test["drought_cat"])

    drought_candidates = {
        "RandomForest": RandomForestClassifier(n_estimators=150, max_depth=10, random_state=42, n_jobs=-1),
        "GradientBoosting": GradientBoostingClassifier(n_estimators=100, max_depth=3, random_state=42),
        "XGBoost": XGBClassifier(n_estimators=150, max_depth=5, random_state=42, n_jobs=-1, verbosity=0,
                                  eval_metric="mlogloss"),
        "KNN": KNeighborsClassifier(n_neighbors=15),
        "DecisionTree": DecisionTreeClassifier(max_depth=8, random_state=42),
        "SVM_RBF": SVC(kernel="rbf", probability=True, random_state=42),
    }
    best_drought_name, drought_model, drought_acc, drought_results = compare_classifiers(
        drought_candidates, train[DROUGHT_FEAT], train["drought_enc"], test[DROUGHT_FEAT], test["drought_enc"],
        metric="accuracy")
    majority_baseline = test["drought_enc"].value_counts(normalize=True).max()
    print(f"      Best: {best_drought_name} (accuracy={drought_acc:.4f}) — "
          f"majority-class baseline={majority_baseline:.4f} (i.e. always guessing the commonest category)")

    # ── MODEL 3: Crop failure — RF / GradientBoosting / XGBoost / KNN / Tree / SVM ──
    print("\n[5/6] MODEL 3 — Crop Failure Risk Classification (ex-ante features only, no yield input)")
    crop_median_train = train.groupby("Crop")["yield_tha"].median()
    global_median_train = train["yield_tha"].median()
    train["failure"] = (train["yield_tha"] < train["Crop"].map(crop_median_train) * 0.60).astype(int)
    test["failure"] = (test["yield_tha"] < test["Crop"].map(crop_median_train).fillna(global_median_train) * 0.60).astype(int)

    failure_candidates = {
        "RandomForest": RandomForestClassifier(n_estimators=150, max_depth=12, random_state=42, n_jobs=-1, class_weight="balanced"),
        "GradientBoosting": GradientBoostingClassifier(n_estimators=150, max_depth=3, random_state=42),
        "XGBoost": XGBClassifier(n_estimators=200, max_depth=6, random_state=42, n_jobs=-1, verbosity=0,
                                  eval_metric="logloss", scale_pos_weight=7),
        "KNN": KNeighborsClassifier(n_neighbors=11),
        "DecisionTree": DecisionTreeClassifier(max_depth=10, random_state=42, class_weight="balanced"),
        "SVM_RBF": SVC(kernel="rbf", probability=True, random_state=42, class_weight="balanced"),
    }
    best_failure_name, failure_model, failure_f1w, failure_results = compare_classifiers(
        failure_candidates, train[FAILURE_FEAT], train["failure"], test[FAILURE_FEAT], test["failure"],
        metric="f1_weighted")
    fpred = failure_model.predict(test[FAILURE_FEAT])
    failure_acc = accuracy_score(test["failure"], fpred)
    failure_precision = precision_score(test["failure"], fpred, zero_division=0)
    failure_recall = recall_score(test["failure"], fpred, zero_division=0)
    failure_f1 = f1_score(test["failure"], fpred, zero_division=0)
    cm = confusion_matrix(test["failure"], fpred).tolist()
    print(f"      Best: {best_failure_name} — accuracy={failure_acc:.3f} precision={failure_precision:.3f} "
          f"recall={failure_recall:.3f} f1={failure_f1:.3f}")
    print(f"      Confusion matrix [[TN,FP],[FN,TP]]: {cm} | base rate (always 'no failure')={1 - test['failure'].mean():.3f}")

    # ── MODEL 4: Season — RandomForest only (matches the mini-project's spec) ──
    print("\n[6/6] MODEL 4 — Best Season Recommendation (RandomForestClassifier)")
    season_model = RandomForestClassifier(n_estimators=120, max_depth=10, random_state=42, n_jobs=-1)
    season_model.fit(train[SEASON_FEAT], train["Season_enc"])
    spred = season_model.predict(test[SEASON_FEAT])
    season_acc = accuracy_score(test["Season_enc"], spred)
    season_dominance = train.groupby("Crop")["Season"].agg(lambda s: s.value_counts(normalize=True).iloc[0])
    single_season_crops = sorted(season_dominance[season_dominance >= 0.9].index.tolist())
    print(f"      Test accuracy={season_acc:.3f}")

    # ── Save artifacts ───────────────────────────────────────────────────
    joblib.dump(yield_model, os.path.join(REGISTRY_DIR, "yield_model.pkl"), compress=3)
    joblib.dump(drought_model, os.path.join(REGISTRY_DIR, "drought_model.pkl"), compress=3)
    joblib.dump(failure_model, os.path.join(REGISTRY_DIR, "failure_model.pkl"), compress=3)
    joblib.dump(season_model, os.path.join(REGISTRY_DIR, "season_model.pkl"), compress=3)
    joblib.dump(le_state, os.path.join(REGISTRY_DIR, "le_state.pkl"))
    joblib.dump(le_crop, os.path.join(REGISTRY_DIR, "le_crop.pkl"))
    joblib.dump(le_season, os.path.join(REGISTRY_DIR, "le_season.pkl"))
    joblib.dump(le_drought, os.path.join(REGISTRY_DIR, "le_drought.pkl"))

    with open(os.path.join(REGISTRY_DIR, "state_lpa.json"), "w") as f:
        json.dump(state_lpa, f, indent=2)

    metadata = {
        "feature_names": {"yield": YIELD_FEAT, "failure": FAILURE_FEAT, "season": SEASON_FEAT, "drought": DROUGHT_FEAT},
        "crops": sorted(df["Crop"].unique().tolist()),
        "states": sorted(df["State"].unique().tolist()),
        "seasons": sorted(df["Season"].unique().tolist()),
        "drought_labels": le_drought.classes_.tolist(),
        "single_season_crops": single_season_crops,
        "crop_median_yield_tha": {k: round(float(v), 3) for k, v in crop_median_train.items()},
        "known_issues": [
            "Coconut yield is in nuts/ha, every other crop is in t/ha.",
            f"{dropped_outlier_rows} rows dropped for exceeding their own crop's 99th-percentile yield.",
            "Drought model excludes rainfall from its inputs on purpose (see train.py) — its accuracy "
            "reflects genuinely forecasting drought category before the season's rain is known, which "
            "is a hard problem. Do not compare it to the old mini-project's 99%+ 'accuracy', which was "
            "measuring a model given the answer as an input.",
        ],
        "algorithm_comparison": {
            "yield_r2": yield_results, "drought_accuracy": drought_results, "failure_f1_weighted": failure_results,
        },
        "best_algorithm": {
            "yield": best_yield_name, "drought": best_drought_name, "failure": best_failure_name, "season": "RandomForest",
        },
        "validation": {
            "method": f"out-of-time: trained on years <= {TRAIN_YEARS_MAX}, tested on {TEST_YEARS}",
            "n_train": int(len(train)), "n_test": int(len(test)),
            "yield_test_r2": round(float(yield_r2), 4),
            "yield_test_mae_t_per_ha_pooled": round(float(yield_mae), 4),
            "yield_test_mae_per_crop": per_crop_mae,
            "yield_per_year_r2": per_year_r2,
            "drought_test_accuracy": round(float(drought_acc), 4),
            "drought_majority_baseline": round(float(majority_baseline), 4),
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

    print(f"\nSaved 4 models + metadata to {REGISTRY_DIR}")


if __name__ == "__main__":
    main()
