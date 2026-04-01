# 🛰️ AgroSentinel India
### ML-Powered Agricultural Risk Intelligence System

<div align="center">

![AgroSentinel Banner](https://img.shields.io/badge/AgroSentinel-India-2d8a52?style=for-the-badge&logo=leaf&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![React](https://img.shields.io/badge/React-18.2-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![Flask](https://img.shields.io/badge/Flask-3.1-000000?style=for-the-badge&logo=flask&logoColor=white)
![XGBoost](https://img.shields.io/badge/XGBoost-3.2-FF6600?style=for-the-badge&logo=xgboost&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**SDG 2 — Zero Hunger &nbsp;|&nbsp; SDG 15 — Life on Land**

*Predicting Agricultural Risks for 600 Million Indian Farmers*

[🚀 Live Demo](#) &nbsp;|&nbsp; [📄 Report](#) &nbsp;|&nbsp; [🎥 Video Demo](#) &nbsp;|&nbsp; [📊 Dataset](#)

</div>

---

## 📌 Table of Contents

- [About the Project](#-about-the-project)
- [SDG Goals](#-sdg-goals)
- [Features](#-features)
- [ML Models & Algorithms](#-ml-models--algorithms)
- [Dataset](#-dataset)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Installation & Setup](#-installation--setup)
- [Running the Project](#-running-the-project)
- [API Endpoints](#-api-endpoints)
- [Screenshots](#-screenshots)
- [Results & Accuracy](#-results--accuracy)
- [Student Info](#-student-info)

---

## 🌾 About the Project

**AgroSentinel India** is an end-to-end Machine Learning system that provides **district-level agricultural risk intelligence** for Indian farmers and policymakers using exclusively **Indian Government datasets**.

India loses **40–50% of agricultural productivity** annually due to unpredicted droughts, floods, and soil degradation — affecting **600 million+ farmers** with no early warning system. AgroSentinel India solves this by predicting:

| Module | What It Predicts | Data Source |
|--------|-----------------|-------------|
| 🌾 **Yield Prediction** | Crop yield in tonnes/hectare | IMD + Agri Census |
| 🌵 **Drought Risk** | High / Medium / Low drought risk | IMD Rainfall Data |
| ⚠️ **Crop Failure Risk** | Probability of crop failure % | PMFBY Insurance Data |
| 📅 **Season Recommendation** | Best planting season for maximum yield | Historical Crop Data |
| 💰 **Live Market Price** | Real-time mandi prices | Agmarknet (data.gov.in) |
| 🌤️ **Live Weather** | Current temperature, humidity, rainfall | Open-Meteo API |

---

## 🌍 SDG Goals

<table>
<tr>
<td width="50%">

### 🌾 SDG 2 — Zero Hunger
- Predicts crop yield before planting season
- Helps farmers choose the right crop and season
- Reduces food loss through early drought/failure alerts
- Live market prices help farmers get fair value

</td>
<td width="50%">

### 🌳 SDG 15 — Life on Land
- Drought risk prediction prevents land degradation
- Crop failure alerts protect soil health
- Season recommendations reduce over-farming stress
- Rainfall analysis supports sustainable land use

</td>
</tr>
</table>

---

## ✨ Features

- 🤖 **4 AI Models** — Yield, Drought, Failure, Season — all trained and compared
- 📊 **6 Algorithms Compared** — Random Forest, XGBoost, Gradient Boosting, SVM, KNN, Linear Regression
- 🏆 **Best Model Auto-Selected** — Highest accuracy model saved automatically
- 📡 **Live Agmarknet Prices** — Real mandi prices from data.gov.in API
- 🌤️ **Live Weather** — Temperature, humidity, precipitation from Open-Meteo
- 🌐 **6 Indian Languages** — English, Hindi, Tamil, Telugu, Kannada, Malayalam
- 📄 **PDF Report Export** — Full prediction report with all results
- 🔄 **Model Retraining** — Retrain all 4 models from the dashboard without restart
- 📋 **Prediction History** — Last 10 predictions saved in session
- 🌙 **Dark / Light Mode** — Full theme switching
- 🐳 **Docker Ready** — Containerized deployment
- ☁️ **PythonAnywhere Deploy** — Cloud hosting ready

---

## 🤖 ML Models & Algorithms

### Model Comparison (6 Algorithms per Model)

```
MODEL 1 — Crop Yield Prediction (Regression)
├── Random Forest Regressor      ← Best (R² = 0.97+)
├── XGBoost Regressor
├── Ridge Regression
└── Linear Regression

MODEL 2 — Drought Risk Classification
├── Random Forest Classifier     ← Best (Acc = 99%+)
├── Gradient Boosting Classifier
├── XGBoost Classifier
├── K-Nearest Neighbors
├── Decision Tree
└── Support Vector Machine (RBF)

MODEL 3 — Crop Failure Risk Classification
├── Random Forest Classifier     ← Best (Acc = 98%+)
├── Gradient Boosting Classifier
├── XGBoost Classifier
├── K-Nearest Neighbors
├── Decision Tree
└── Support Vector Machine (RBF)

MODEL 4 — Best Season Recommendation
└── Random Forest Classifier     (Acc = 95%+)
```

### Evaluation Metrics
- **Classification**: Accuracy Score, 5-Fold Cross Validation, Confusion Matrix
- **Regression**: R² Score, RMSE (Root Mean Square Error)
- **Explainability**: SHAP Values (feature importance)

---

## 📂 Dataset

### Data Sources (All Indian Government)

| Source | Description | URL |
|--------|-------------|-----|
| **IMD** — India Meteorological Dept | Rainfall 1901–2015, state-wise | data.gov.in |
| **Agri Census** | Crop production, area, yield | data.gov.in |
| **PMFBY** | Crop insurance, failure data | pmfby.gov.in |
| **Agmarknet** | Live mandi prices | agmarknet.gov.in |
| **Open-Meteo** | Live weather data | open-meteo.com |

### Dataset Statistics

```
crop_production.csv    →  2,36,449 records  |  7 columns
crop_yield.csv         →  15,900 records    |  7 columns
rainfall_1901-2015.csv →  115 years         |  15 columns

Master Dataset (after merge):
  Total Records  : 2,36,449
  Crops Covered  : 105 unique crops
  States Covered : 33 Indian states + UTs
  Years Covered  : 1997 – 2015
```

### Key Features Used

| Feature | Description | Unit |
|---------|-------------|------|
| `state_enc` | Encoded state name | Categorical |
| `crop_enc` | Encoded crop name | Categorical |
| `season_enc` | Encoded season | Categorical |
| `year` | Year of record | YYYY |
| `avg_rainfall` | Annual rainfall from IMD | mm |
| `yield_val` | Crop yield (target) | tonnes/hectare |
| `drought_risk` | Derived from rainfall SPI | High/Medium/Low |
| `crop_failure` | Binary — yield < 60% median | 0 or 1 |

---

## 🛠️ Tech Stack

### Backend
```
Python 3.11
Flask 3.1.3          — REST API framework
Flask-CORS 6.0.2     — Cross-origin support
scikit-learn         — ML algorithms
XGBoost 3.2.0        — Gradient boosting
joblib               — Model persistence
pandas 3.0.1         — Data processing
numpy                — Numerical operations
matplotlib 3.10.8    — EDA visualizations
seaborn              — Statistical plots
requests             — Live API calls
```

### Frontend
```
React 18.2           — UI framework
framer-motion 11.0   — Animations
chart.js 4.4         — Charts (Bar, Doughnut)
react-chartjs-2 5.2  — Chart React wrappers
axios 1.6            — API calls
jsPDF 2.5            — PDF report generation
jspdf-autotable 3.8  — PDF tables
```

### Data & APIs
```
Agmarknet API        — Live mandi prices (data.gov.in)
Open-Meteo API       — Live weather (free, no key)
data.gov.in          — Government datasets
```

---

## 📁 Project Structure

```
AgroSentinel India/
│
├── 📂 datasets/
│   ├── crop_production.csv
│   ├── crop_yield.csv
│   └── rainfall in india 1901-2015.csv
│
├── 📂 ml_models/
│   ├── train_model.py          ← Training pipeline (6 algorithms)
│   ├── yield_model.pkl         ← Saved best yield model
│   ├── drought_model.pkl       ← Saved best drought model
│   ├── failure_model.pkl       ← Saved best failure model
│   ├── season_model.pkl        ← Saved season model
│   ├── metadata.pkl            ← Crops, states, stats
│   ├── le_crop.pkl             ← Label encoder
│   ├── le_state.pkl            ← Label encoder
│   ├── le_season.pkl           ← Label encoder
│   └── le_drought.pkl          ← Label encoder
│
├── 📂 backend/
│   └── app.py                  ← Flask REST API (12 endpoints)
│
├── 📂 frontend/
│   ├── package.json
│   ├── 📂 public/
│   │   └── index.html
│   └── 📂 src/
│       ├── index.js
│       └── App.js              ← Complete React dashboard
│
├── 📂 notebooks/
│   └── eda_dashboard.png       ← EDA charts (auto-generated)
│
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## ⚙️ Installation & Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- npm 9+
- Git

### Step 1 — Clone Repository
```bash
git clone https://github.com/gbabhi125-svg/agrosentinel-india.git
cd agrosentinel-india
```

### Step 2 — Python Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / Mac
source venv/bin/activate
```

### Step 3 — Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Install Node Dependencies
```bash
cd frontend
npm install
cd ..
```

---

## 🚀 Running the Project

### Step 1 — Train ML Models
```bash
python ml_models/train_model.py
```
This will:
- Load all 3 datasets
- Clean and merge data
- Train 4 models (6 algorithms each)
- Auto-select best algorithm
- Save all `.pkl` model files
- Generate `notebooks/eda_dashboard.png`

Expected output:
```
MODEL 1 — Crop Yield Prediction
   Random Forest     R²=0.9743  RMSE=1.23
   XGBoost           R²=0.9681  RMSE=1.41
   ★ Best: Random Forest (R²=0.9743)

MODEL 2 — Drought Risk Classification
   Random Forest     Acc=99.84%
   XGBoost           Acc=99.51%
   ★ Best: Random Forest (Acc=99.84%)
```

### Step 2 — Start Flask API
```bash
python backend/app.py
```
API will start at: `http://127.0.0.1:5000`

### Step 3 — Start React Frontend
```bash
cd frontend
npm start
```
Dashboard opens at: `http://localhost:3000`

### ✅ You're ready! Open `http://localhost:3000`

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check + endpoint list |
| `GET` | `/api/crops` | List of all 105 crops |
| `GET` | `/api/states` | List of all 33 states |
| `GET` | `/api/stats` | Model accuracy statistics |
| `POST` | `/api/predict-all` | All 4 predictions in one call |
| `POST` | `/api/predict-yield` | Crop yield prediction |
| `POST` | `/api/predict-drought` | Drought risk prediction |
| `POST` | `/api/predict-failure` | Crop failure risk |
| `POST` | `/api/predict-season` | Best season recommendation |
| `GET` | `/api/market-price/<crop>` | Live mandi price |
| `GET` | `/api/weather/<state>` | Live weather data |
| `POST` | `/api/retrain` | Retrain all models |
| `GET` | `/api/retrain-status` | Retraining progress |

### Sample API Request

```bash
curl -X POST http://127.0.0.1:5000/api/predict-all \
  -H "Content-Type: application/json" \
  -d '{
    "state": "Gujarat",
    "crop": "Banana",
    "season": "Whole Year",
    "year": 2026,
    "rainfall": 820
  }'
```

### Sample Response
```json
{
  "yield": {
    "predicted_yield": 62.17,
    "yield_per_acre": 25.16,
    "unit": "tonnes/hectare",
    "grade": "Excellent",
    "color": "success"
  },
  "drought": {
    "risk": "Medium",
    "confidence": 89.3,
    "advice": "Below-average rainfall — monitor reserves + plan supplemental irrigation."
  },
  "failure": {
    "risk": "Low Risk",
    "probability": 0.0,
    "color": "success"
  },
  "season": {
    "best_season": "Whole Year",
    "confidence": 93.2
  },
  "summary": "Banana in Gujarat (Whole Year 2026) — Yield:62.17 t/ha | Drought:Medium | Failure:Low Risk"
}
```

---

## 📸 Screenshots

> Dashboard — Dark Mode with Live Results

```
┌─────────────────────────────────────────────────┐
│  🛰️  AgroSentinel India                          │
│  ML-Powered Agricultural Risk Intelligence       │
│  📋 236K Records | 🌾 105 Crops | 🗺️ 33 States   │
├─────────────────────────────────────────────────┤
│  STATE: Gujarat    CROP: Banana   SEASON: Whole  │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │ 📈 62.17 │ │ 🌵 Medium│ │ ⚠️ Low Risk  0%  │ │
│  │ t/ha     │ │ Drought  │ │ Failure Risk     │ │
│  │ Excellent│ │ 89% conf │ └──────────────────┘ │
│  └──────────┘ └──────────┘ ┌──────────────────┐ │
│  💰 ₹2115/quintal (Live)   │ 📅 Whole Year 93%│ │
│  🌤️ 28°C | 66% humidity   └──────────────────┘ │
└─────────────────────────────────────────────────┘
```

---

## 📊 Results & Accuracy

| Model | Algorithm | Metric | Score |
|-------|-----------|--------|-------|
| Yield Prediction | Random Forest | R² Score | **0.9743** |
| Drought Risk | Random Forest | Accuracy | **99.84%** |
| Crop Failure Risk | Random Forest | Accuracy | **98.21%** |
| Season Recommendation | Random Forest | Accuracy | **95.67%** |

### EDA Dashboard
The training script auto-generates a 6-panel EDA dashboard at `notebooks/eda_dashboard.png`:
- Top 15 crops by record count
- Yield distribution histogram
- Drought risk pie chart
- Top 10 states by average yield
- Drought model accuracy comparison
- Failure model accuracy comparison

---

## 🐳 Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build

# Access at:
# Frontend: http://localhost:3000
# Backend:  http://localhost:5000
```

---

## ☁️ PythonAnywhere Deployment

```bash
# 1. Upload project to PythonAnywhere
# 2. Create virtual environment
mkvirtualenv agrosentinel --python=python3.11

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure WSGI file to point to backend/app.py
# 5. Set static files for React build
npm run build
```

---

## 👨‍🎓 Student Info

| Field | Details |
|-------|---------|
| **Name** | GB Abhilash |
| **SRN** | PES1PG25CA064 |
| **Course** | MCA — Master of Computer Applications |
| **Institution** | PESU Academy, Bangalore |
| **Faculty Guide** | Dr. S. Thenmozhi |
| **Academic Year** | 2025–26 |
| **SDG Goals** | SDG 2 (Zero Hunger) + SDG 15 (Life on Land) |
| **Domain** | Agriculture + Machine Learning |

---

## 📋 Requirements.txt

```
flask==3.1.3
flask-cors==6.0.2
pandas==3.0.1
numpy>=1.24.0
scikit-learn>=1.3.0
xgboost==3.2.0
joblib>=1.3.0
matplotlib==3.10.8
seaborn>=0.12.0
requests>=2.31.0
```

---

## 🤝 Acknowledgements

- **India Meteorological Department (IMD)** — Rainfall dataset
- **data.gov.in** — Open Government Data Platform India
- **Agmarknet** — Agricultural Marketing Information Network
- **Open-Meteo** — Open-source weather API
- **PMFBY** — Pradhan Mantri Fasal Bima Yojana

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**🌾 AgroSentinel India — Empowering Indian Farmers with AI**

Made with ❤️ for Indian Agriculture | SDG 2 🌾 | SDG 15 🌳

⭐ Star this repository if it helped you!

</div>
