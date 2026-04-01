import pandas as pd
import numpy as np
import os
import joblib
import warnings
warnings.filterwarnings('ignore')

from sklearn.ensemble import (RandomForestClassifier, RandomForestRegressor,
                               GradientBoostingClassifier, GradientBoostingRegressor,
                               ExtraTreesClassifier)
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, r2_score, mean_squared_error
from xgboost import XGBClassifier, XGBRegressor
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ── Paths ──────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DS_DIR      = os.path.join(BASE_DIR, "datasets")
MODEL_DIR   = os.path.join(BASE_DIR, "ml_models")
NB_DIR      = os.path.join(BASE_DIR, "notebooks")
os.makedirs(NB_DIR, exist_ok=True)

print("="*65)
print("  AgroSentinel India — ML Training Pipeline v2.0")
print("="*65)

# ══════════════════════════════════════════════════════════════
# STEP 1 — LOAD DATASETS
# ══════════════════════════════════════════════════════════════
print("\n📂 STEP 1: Loading datasets...")

prod_df  = pd.read_csv(os.path.join(DS_DIR, "crop_production.csv"))
yield_df = pd.read_csv(os.path.join(DS_DIR, "crop_yield.csv"))
rain_df  = pd.read_csv(os.path.join(DS_DIR, "rainfall in india 1901-2015.csv"))

print(f"  crop_production  : {prod_df.shape[0]:,} rows × {prod_df.shape[1]} cols")
print(f"  crop_yield       : {yield_df.shape[0]:,} rows × {yield_df.shape[1]} cols")
print(f"  rainfall         : {rain_df.shape[0]:,} rows × {rain_df.shape[1]} cols")

# ══════════════════════════════════════════════════════════════
# STEP 2 — PREPROCESS CROP PRODUCTION
# ══════════════════════════════════════════════════════════════
print("\n🔧 STEP 2: Preprocessing crop_production...")

prod_df.columns = (prod_df.columns.str.strip()
                                  .str.lower()
                                  .str.replace(' ','_')
                                  .str.replace('-','_'))

rename_prod = {}
for c in prod_df.columns:
    if   'state'      in c: rename_prod[c] = 'state'
    elif 'district'   in c: rename_prod[c] = 'district'
    elif 'year'       in c: rename_prod[c] = 'year'
    elif 'season'     in c: rename_prod[c] = 'season'
    elif 'crop'       in c and 'name' not in c: rename_prod[c] = 'crop'
    elif 'area'       in c: rename_prod[c] = 'area'
    elif 'production' in c: rename_prod[c] = 'production'
prod_df.rename(columns=rename_prod, inplace=True)
print(f"  Renamed columns: {list(prod_df.columns)}")

for col in ['area','production','year']:
    if col in prod_df.columns:
        prod_df[col] = pd.to_numeric(prod_df[col], errors='coerce')

prod_df.dropna(subset=['state','crop','area','production'], inplace=True)
prod_df = prod_df[(prod_df['production'] > 0) & (prod_df['area'] > 0)]
prod_df['yield_tha'] = prod_df['production'] / prod_df['area']

q99 = prod_df['yield_tha'].quantile(0.99)
prod_df = prod_df[prod_df['yield_tha'] <= q99]

prod_df['state']  = prod_df['state'].astype(str).str.strip().str.title()
prod_df['crop']   = prod_df['crop'].astype(str).str.strip().str.title()
if 'season' in prod_df.columns:
    prod_df['season'] = prod_df['season'].astype(str).str.strip().str.title()
else:
    prod_df['season'] = 'Kharif'

print(f"  After cleaning   : {prod_df.shape[0]:,} rows")
print(f"  Unique states    : {prod_df['state'].nunique()}")
print(f"  Unique crops     : {prod_df['crop'].nunique()}")

# ══════════════════════════════════════════════════════════════
# STEP 3 — RAINFALL
# ══════════════════════════════════════════════════════════════
print("\n🔧 STEP 3: Preprocessing rainfall...")

rain_df.columns = rain_df.columns.str.strip().str.upper()
months = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']
avail  = [m for m in months if m in rain_df.columns]
rain_df['annual'] = rain_df[avail].sum(axis=1)

state_col = next((c for c in rain_df.columns
                  if 'SUBDIVISION' in c or 'STATE' in c or 'REGION' in c), None)
if state_col:
    rain_state = rain_df.groupby(state_col)['annual'].mean().reset_index()
    rain_state.columns = ['state_key','avg_rainfall']
    print(f"  Rainfall by region: {len(rain_state)} entries")
else:
    print("  No state column — using fallback values")

# ══════════════════════════════════════════════════════════════
# STEP 4 — MASTER DATAFRAME
# ══════════════════════════════════════════════════════════════
print("\n🔗 STEP 4: Building master dataset...")

df = prod_df.copy()

FALLBACK_RAIN = {
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
df['rainfall'] = df['state'].map(FALLBACK_RAIN).fillna(1000).astype(float)

if 'year' not in df.columns:
    df['year'] = 2010
df['year'] = pd.to_numeric(df['year'], errors='coerce').fillna(2010).astype(int)

def drought_label(r):
    if   r < 500:  return 'High'
    elif r < 900:  return 'Medium'
    else:          return 'Low'
df['drought_risk'] = df['rainfall'].apply(drought_label)

crop_med = df.groupby('crop')['yield_tha'].transform('median')
df['crop_failure'] = (df['yield_tha'] < crop_med * 0.60).astype(int)

print(f"  Master shape     : {df.shape}")
print(f"  States           : {df['state'].nunique()}")
print(f"  Crops            : {df['crop'].nunique()}")
print(f"  Seasons          : {df['season'].unique().tolist()}")
print(f"  Drought dist:\n{df['drought_risk'].value_counts().to_string()}")
print(f"  Failure rate     : {df['crop_failure'].mean()*100:.1f}%")

# ══════════════════════════════════════════════════════════════
# STEP 5 — ENCODE
# ══════════════════════════════════════════════════════════════
print("\n🔢 STEP 5: Encoding categorical features...")

le_state   = LabelEncoder()
le_crop    = LabelEncoder()
le_season  = LabelEncoder()
le_drought = LabelEncoder()

df['state_enc']   = le_state.fit_transform(df['state'])
df['crop_enc']    = le_crop.fit_transform(df['crop'])
df['season_enc']  = le_season.fit_transform(df['season'])
df['drought_enc'] = le_drought.fit_transform(df['drought_risk'])

joblib.dump(le_state,   os.path.join(MODEL_DIR,"le_state.pkl"))
joblib.dump(le_crop,    os.path.join(MODEL_DIR,"le_crop.pkl"))
joblib.dump(le_season,  os.path.join(MODEL_DIR,"le_season.pkl"))
joblib.dump(le_drought, os.path.join(MODEL_DIR,"le_drought.pkl"))
print("  ✅ Label encoders saved")

YIELD_FEAT   = ['state_enc','crop_enc','season_enc','year','rainfall']
DROUGHT_FEAT = ['state_enc','crop_enc','season_enc','year','rainfall']
FAILURE_FEAT = ['state_enc','crop_enc','season_enc','year','rainfall','yield_tha']
SEASON_FEAT  = ['state_enc','crop_enc','rainfall','year']

joblib.dump({
    'yield':   YIELD_FEAT,
    'drought': DROUGHT_FEAT,
    'failure': FAILURE_FEAT,
    'season':  SEASON_FEAT,
}, os.path.join(MODEL_DIR,"feature_names.pkl"))
print("  ✅ Feature names saved")

# ══════════════════════════════════════════════════════════════
# STEP 6 — MODEL 1: YIELD PREDICTION
# ══════════════════════════════════════════════════════════════
print("\n"+"="*65)
print("MODEL 1 — Crop Yield Prediction (Regression)")
print("="*65)

X = df[YIELD_FEAT].values
y = df['yield_tha'].values
Xtr,Xte,ytr,yte = train_test_split(X, y, test_size=0.2, random_state=42)
print(f"  Train: {len(Xtr):,}  Test: {len(Xte):,}")

yield_candidates = {
    "Random Forest Regressor":     RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1),
    "XGBoost Regressor":           XGBRegressor(n_estimators=200, random_state=42, verbosity=0),
    "Gradient Boosting Regressor": GradientBoostingRegressor(n_estimators=150, random_state=42),
    "Ridge Regression":            Ridge(alpha=1.0),
    "Linear Regression":           LinearRegression(),
}

best_r2 = -999; best_yield = None; best_yname = ""; yield_res = {}

for name, model in yield_candidates.items():
    print(f"  Training {name}...", flush=True)
    model.fit(Xtr, ytr)
    pred = model.predict(Xte)
    r2   = r2_score(yte, pred)
    rmse = np.sqrt(mean_squared_error(yte, pred))
    yield_res[name] = r2
    print(f"  {name:<35} R²={r2:.4f}  RMSE={rmse:.4f}")
    if r2 > best_r2:
        best_r2 = r2; best_yield = model; best_yname = name

print(f"\n  ★ Best: {best_yname}  R²={best_r2:.4f}")
joblib.dump(best_yield, os.path.join(MODEL_DIR,"yield_model.pkl"))
print("  ✅ yield_model.pkl saved")

# ══════════════════════════════════════════════════════════════
# STEP 7 — MODEL 2: DROUGHT RISK
# SVM removed — hangs on 200k+ rows (O(n²) kernel computation)
# Replaced with ExtraTreesClassifier (faster, comparable accuracy)
# ══════════════════════════════════════════════════════════════
print("\n"+"="*65)
print("MODEL 2 — Drought Risk Classification")
print("="*65)

X2 = df[DROUGHT_FEAT].values
y2 = df['drought_enc'].values
X2tr,X2te,y2tr,y2te = train_test_split(X2, y2, test_size=0.2, random_state=42)

drought_candidates = {
    "Random Forest":     RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1),
    "XGBoost":           XGBClassifier(n_estimators=150, random_state=42, verbosity=0, eval_metric='mlogloss'),
    "Gradient Boosting": GradientBoostingClassifier(n_estimators=150, random_state=42),
    "Extra Trees":       ExtraTreesClassifier(n_estimators=200, random_state=42, n_jobs=-1),
    "KNN":               KNeighborsClassifier(n_neighbors=7, n_jobs=-1),
    "Decision Tree":     DecisionTreeClassifier(max_depth=10, random_state=42),
}

best_dr_acc = 0; best_drought = None; best_drname = ""; drought_res = {}

for name, model in drought_candidates.items():
    print(f"  Training {name}...", flush=True)
    model.fit(X2tr, y2tr)
    pred = model.predict(X2te)
    acc  = accuracy_score(y2te, pred)
    drought_res[name] = acc
    print(f"  {name:<22} Accuracy={acc*100:.2f}%")
    if acc > best_dr_acc:
        best_dr_acc = acc; best_drought = model; best_drname = name

print(f"\n  ★ Best: {best_drname}  Acc={best_dr_acc*100:.2f}%")
joblib.dump(best_drought, os.path.join(MODEL_DIR,"drought_model.pkl"))
print("  ✅ drought_model.pkl saved")

# ══════════════════════════════════════════════════════════════
# STEP 8 — MODEL 3: CROP FAILURE
# ══════════════════════════════════════════════════════════════
print("\n"+"="*65)
print("MODEL 3 — Crop Failure Risk Classification")
print("="*65)

X3 = df[FAILURE_FEAT].values
y3 = df['crop_failure'].values
X3tr,X3te,y3tr,y3te = train_test_split(X3, y3, test_size=0.2, random_state=42)

failure_candidates = {
    "Random Forest":     RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1),
    "XGBoost":           XGBClassifier(n_estimators=150, random_state=42, verbosity=0, eval_metric='logloss'),
    "Gradient Boosting": GradientBoostingClassifier(n_estimators=150, random_state=42),
    "Extra Trees":       ExtraTreesClassifier(n_estimators=200, random_state=42, n_jobs=-1),
    "KNN":               KNeighborsClassifier(n_neighbors=7, n_jobs=-1),
    "Decision Tree":     DecisionTreeClassifier(max_depth=10, random_state=42),
}

best_fl_acc = 0; best_failure = None; best_flname = ""; failure_res = {}

for name, model in failure_candidates.items():
    print(f"  Training {name}...", flush=True)
    model.fit(X3tr, y3tr)
    pred = model.predict(X3te)
    acc  = accuracy_score(y3te, pred)
    failure_res[name] = acc
    print(f"  {name:<22} Accuracy={acc*100:.2f}%")
    if acc > best_fl_acc:
        best_fl_acc = acc; best_failure = model; best_flname = name

print(f"\n  ★ Best: {best_flname}  Acc={best_fl_acc*100:.2f}%")
joblib.dump(best_failure, os.path.join(MODEL_DIR,"failure_model.pkl"))
print("  ✅ failure_model.pkl saved")

# ══════════════════════════════════════════════════════════════
# STEP 9 — MODEL 4: SEASON RECOMMENDATION
# ══════════════════════════════════════════════════════════════
print("\n"+"="*65)
print("MODEL 4 — Best Season Recommendation")
print("="*65)

X4 = df[SEASON_FEAT].values
y4 = df['season_enc'].values
X4tr,X4te,y4tr,y4te = train_test_split(X4, y4, test_size=0.2, random_state=42)

print("  Training Random Forest season model...", flush=True)
season_model = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
season_model.fit(X4tr, y4tr)
sea_acc = accuracy_score(y4te, season_model.predict(X4te))
print(f"  Season Model Accuracy: {sea_acc*100:.2f}%")
joblib.dump(season_model, os.path.join(MODEL_DIR,"season_model.pkl"))
print("  ✅ season_model.pkl saved")

# ══════════════════════════════════════════════════════════════
# STEP 10 — SAVE METADATA
# ══════════════════════════════════════════════════════════════
print("\n💾 STEP 10: Saving metadata...")

meta = {
    'crops':   sorted(df['crop'].unique().tolist()),
    'states':  sorted(df['state'].unique().tolist()),
    'seasons': sorted(df['season'].unique().tolist()),
    'drought_labels': le_drought.classes_.tolist(),
    'stats': {
        'total_records':      int(len(df)),
        'total_crops':        int(df['crop'].nunique()),
        'total_states':       int(df['state'].nunique()),
        'total_districts':    int(df['district'].nunique()) if 'district' in df.columns else 0,
        'year_range':         f"{int(df['year'].min())} — {int(df['year'].max())}",
        'yield_mean':         round(float(df['yield_tha'].mean()), 4),
        'yield_max':          round(float(df['yield_tha'].max()),  4),
        'best_yield_model':   best_yname,
        'best_yield_r2':      round(float(best_r2),     4),
        'best_drought_model': best_drname,
        'best_drought_acc':   round(float(best_dr_acc), 4),
        'best_failure_model': best_flname,
        'best_failure_acc':   round(float(best_fl_acc), 4),
        'season_acc':         round(float(sea_acc),     4),
    }
}

joblib.dump(meta, os.path.join(MODEL_DIR,"metadata.pkl"))
print("  ✅ metadata.pkl saved")

# ══════════════════════════════════════════════════════════════
# STEP 11 — EDA CHARTS
# ══════════════════════════════════════════════════════════════
print("\n📊 STEP 11: Generating EDA charts...")

fig, axes = plt.subplots(2, 3, figsize=(18, 10))
fig.suptitle('AgroSentinel India — EDA Dashboard', fontsize=16, fontweight='bold')

top15 = df['crop'].value_counts().head(15)
axes[0,0].barh(top15.index[::-1], top15.values[::-1], color='#2d8a52')
axes[0,0].set_title('Top 15 Crops by Records', fontweight='bold')
axes[0,0].set_xlabel('Record Count')

axes[0,1].hist(df['yield_tha'], bins=60, color='#1a5c34', edgecolor='white', alpha=0.85)
axes[0,1].set_title('Yield Distribution (t/ha)', fontweight='bold')
axes[0,1].set_xlabel('Yield (t/ha)')

dr_c = df['drought_risk'].value_counts()
axes[0,2].pie(dr_c.values, labels=dr_c.index, autopct='%1.1f%%',
              colors=['#dc3545','#ffc107','#198754'], startangle=90)
axes[0,2].set_title('Drought Risk Distribution', fontweight='bold')

st_y = df.groupby('state')['yield_tha'].mean().sort_values(ascending=False).head(10)
axes[1,0].bar(range(len(st_y)), st_y.values, color='#0a4a7a')
axes[1,0].set_xticks(range(len(st_y)))
axes[1,0].set_xticklabels(st_y.index, rotation=40, ha='right', fontsize=8)
axes[1,0].set_title('Top 10 States — Avg Yield', fontweight='bold')
axes[1,0].set_ylabel('Avg Yield (t/ha)')

names5 = list(drought_res.keys()); vals5 = [v*100 for v in drought_res.values()]
clrs5  = ['#1a5c34','#2d8a52','#52b788','#74c69d','#b7e4c7','#d8f3dc']
axes[1,1].bar(range(len(names5)), vals5, color=clrs5[:len(names5)])
axes[1,1].set_xticks(range(len(names5)))
axes[1,1].set_xticklabels(names5, rotation=30, ha='right', fontsize=8)
axes[1,1].set_ylim(0,110); axes[1,1].set_title('Drought Model Comparison', fontweight='bold')
for i,v in enumerate(vals5): axes[1,1].text(i, v+1, f'{v:.1f}%', ha='center', fontsize=7)

names6 = list(failure_res.keys()); vals6 = [v*100 for v in failure_res.values()]
clrs6  = ['#b45309','#d97706','#f59e0b','#fbbf24','#fde68a','#fef3c7']
axes[1,2].bar(range(len(names6)), vals6, color=clrs6[:len(names6)])
axes[1,2].set_xticks(range(len(names6)))
axes[1,2].set_xticklabels(names6, rotation=30, ha='right', fontsize=8)
axes[1,2].set_ylim(0,110); axes[1,2].set_title('Crop Failure Model Comparison', fontweight='bold')
for i,v in enumerate(vals6): axes[1,2].text(i, v+1, f'{v:.1f}%', ha='center', fontsize=7)

plt.tight_layout()
plt.savefig(os.path.join(NB_DIR,"eda_dashboard.png"), dpi=150, bbox_inches='tight')
plt.close()
print("  ✅ EDA chart saved → notebooks/eda_dashboard.png")

# ══════════════════════════════════════════════════════════════
# FINAL SUMMARY
# ══════════════════════════════════════════════════════════════
print("\n"+"="*65)
print("  TRAINING COMPLETE!")
print("="*65)
print(f"  Records   : {len(df):,}")
print(f"  Crops     : {df['crop'].nunique()}")
print(f"  States    : {df['state'].nunique()}")
print(f"\n  Yield     : {best_yname} — R²={best_r2:.4f}")
print(f"  Drought   : {best_drname} — Acc={best_dr_acc*100:.2f}%")
print(f"  Failure   : {best_flname} — Acc={best_fl_acc*100:.2f}%")
print(f"  Season    : Random Forest — Acc={sea_acc*100:.2f}%")
print(f"\n  Saved: yield_model.pkl  drought_model.pkl")
print(f"         failure_model.pkl  season_model.pkl")
print(f"         metadata.pkl  feature_names.pkl")
print("\n✅ Ready for Flask API!")