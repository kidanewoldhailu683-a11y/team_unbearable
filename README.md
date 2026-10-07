# Addis Ride Demand Forecasting Challenge
**Qiyas Data Science & AI Hackathon | Addis Ababa University**

---

## 👥 Team Information (Deliverable G2)
<<<<<<< HEAD
- **Team Name**: `team_unbearable`
=======
- **Team Name**: `team_qiyas_ai`
>>>>>>> 7b6dbf6386ddc7fab4fc8f1a2c81f9cabf215de6
- **Team Members**:
  - **Data Lead**: Data Cleaning, Timezone Alignment & Master Table Integration
  - **Analysis & Viz Lead**: Exploratory Data Analysis, 14 Tasks & 12 Visualization Figures
  - **Modeling Lead**: Time-Series Regressors, Chronological Validation & Model Tuning
  - **Deployment Lead**: Production Streamlit GUI Application, Packaging & Reproducibility
- **Track**: Time-Series Regression & Operational Urban Dispatch Optimization

---

## 📋 Executive Project Summary (Deliverable G2)
This repository contains the complete, production-grade data science and machine learning pipeline for forecasting hourly ride demand across the 12 canonical zones of Addis Ababa, Ethiopia for the official evaluation fortnight of **1–14 November 2025 (4,032 zone-hours)**. Using 85,000 historical trip records (January–October 2025), hourly weather observations, and citywide event calendars, our pipeline resolves 55 noisy raw sub-city spellings into a verified 12-zone dimension (`dim_zone.csv`), empirically proves the weather clock offset from UTC to `Africa/Addis_Ababa` local time (EAT UTC+3), and strictly enforces the fundamental data integrity invariant **ONE ROW = ONE ZONE + ONE HOUR** with zero row inflation. Evaluated using strict chronological validation (18–31 October 2025), our winning **CatBoostRegressor** model achieved **R² = 73.87%**, **MAE = 6.92 trips/hr**, and **RMSE = 15.63**, outperforming seasonal-naive baselines by over 55%. The platform includes an interactive, 10-module Streamlit operational dashboard featuring out-of-sample forecast lookups and live What-If scenario simulations with dynamic Top 10 feature sensitivity tuning.

---

## 📂 Project Directory Structure (Section 6.1)

```text
<<<<<<< HEAD
team_unbearable/
=======
team_qiyas_ai/
>>>>>>> 7b6dbf6386ddc7fab4fc8f1a2c81f9cabf215de6
├── README.md                                  # Setup, run order, summary, demo link (G2)
├── requirements.txt                           # Pinned package versions (G3)
│
├── submission/                                # Scored prediction deliverables (G4)
<<<<<<< HEAD
│   └── team_unbearable_submission.csv           # 4,032 rows, verified columns [row_id, predicted_trips]
=======
│   └── team_qiyas_ai_submission.csv           # 4,032 rows, verified columns [row_id, predicted_trips]
>>>>>>> 7b6dbf6386ddc7fab4fc8f1a2c81f9cabf215de6
│
├── data/                                      # Data storage hierarchy
│   ├── raw/                                   # Immutable original CSV exports (never edited)
│   │   ├── ride_demand_train.csv
│   │   ├── ride_demand_test.csv
│   │   ├── weather_hourly.csv
│   │   ├── events_calendar.csv
│   │   └── submission_template.csv
│   └── processed/                             # Fully cleaned and joined master assets (A8)
│       ├── master_train.csv                   # 84,614 zone-hours with 29 engineered features
│       ├── master_test.csv                    # 4,032 test zone-hours (1–14 Nov 2025)
│       └── data_dictionary_master.csv         # Full schema dictionary with derivations
│
├── notebooks/                                 # Sequential, self-contained Jupyter notebooks
│   ├── 01_cleaning_and_integration.ipynb      # Deliverable A: Data cleaning, clocks, join audits
│   ├── 02_analysis_report.ipynb               # Deliverable B: 14 numbered analytical questions
│   ├── 03_visualizations.ipynb                # Deliverable C: 12 production visualization figures
│   └── 04_modeling_and_evaluation.ipynb       # Deliverable D: Baselines, ablations, CatBoost model
│
├── src/                                       # Modular, reusable pipeline code
│   ├── cleaning.py                            # Raw data parsing, timezone shift, join map
│   ├── features.py                            # Cyclical time, lags, rolling means, interactions
│   ├── train.py                               # Model cross-validation, hyperparameter tuning
│   └── predict.py                             # Generation of final submission predictions
│
├── models/                                    # Serialized model artifacts
│   └── final_model.joblib                     # Production CatBoost pipeline artifact (780 KB)
│
├── figures/                                   # Task C: 12 Figures (PNG, >=150 DPI) + Captions
│   ├── fig01_gaps_and_missingness.png         # Audit of raw missingness and sensor dropouts
│   ├── fig02_before_after_cleaning.png        # Temperature & trip distributions before/after
│   ├── fig03_demand_trend_with_holidays.png   # 10-month citywide trend with holiday markers
│   ├── fig04_hour_by_weekday_heatmap.png      # 24h diurnal demand heatmap across weekdays
│   ├── fig05_zone_profiles.png                # Zone demand profiles by operational typology
│   ├── fig06_weather_timezone_check.png       # Empirical proof of UTC to EAT UTC+3 weather shift
│   ├── fig07_rain_effect.png                  # Rainfall dose-response across severity classes
│   ├── fig08_event_study.png                  # Event-window demand uplift (-2h, during, +2h)
│   ├── fig09_holiday_effects.png              # Public holiday impact index vs standard days
│   ├── fig10_model_comparison.png             # 10-model benchmark validation comparison
│   ├── fig11_forecast_vs_actual.png           # Fortnight validation forecast vs ground truth
│   ├── fig12_feature_importance.png           # Top 12 feature importance weights from CatBoost
│   └── figure_captions.md                     # Descriptions and takeaways for all 12 figures
│
├── reports/                                   # Written report deliverables (PDF / Markdown)
│   ├── A_cleaning_and_integration.md          # Comprehensive cleaning log, audits & join proofs
│   ├── B_analysis_report.md                   # 14 numbered analytical tasks (B1.1 through B4.3)
│   └── D_model_evaluation.md                  # Baselines, ablations, leakage audit, diagnostics
│
├── app/                                       # Deployed Forecast Demo (Deliverable E)
│   ├── app.py                                 # Streamlit production web application
│   ├── requirements.txt                       # Streamlit application dependencies
│   └── assets/                                # Bundled lookup tables and final model
│
└── presentation/                              # 5-Slide Presentation Deck (Deliverable F)
<<<<<<< HEAD
    ├── team_unbearable_slides.pptx              # Presentation deck in PowerPoint format
    └── team_unbearable_slides.pdf               # Presentation deck in PDF format
=======
    ├── team_unbearable_slides.pptx            # 5-slide PowerPoint deck for team_unbearable
    ├── team_unbearable_deck.html              # Interactive browser presentation deck
    └── team_unbearable_deck_prompt.md         # Slide specification & AI generator prompt
>>>>>>> 7b6dbf6386ddc7fab4fc8f1a2c81f9cabf215de6
```

---

## 🗺️ Deliverables Location Index (Section 6.2)

| Deliverable | Key Contents & Artifacts | Primary Location |
| :--- | :--- | :--- |
<<<<<<< HEAD
| **Prediction Score** | 4,032 out-of-sample predictions, formatted against official test template | `submission/team_unbearable_submission.csv` |
=======
| **Prediction Score** | 4,032 out-of-sample predictions, formatted against official test template | `submission/team_qiyas_ai_submission.csv` |
>>>>>>> 7b6dbf6386ddc7fab4fc8f1a2c81f9cabf215de6
| **A — Pipeline** | Cleaning log, join map, time-zone proof, 6 automated integrity checks, master files | `reports/A_cleaning_and_integration.md`, `data/processed/`, `notebooks/01_cleaning_and_integration.ipynb` |
| **B — Analysis** | All 14 numbered tasks across Demand, Weather, Events, and Operations | `reports/B_analysis_report.md`, `notebooks/02_analysis_report.ipynb` |
| **C — Visualizations** | 12 high-resolution figures (PNG) + structured interpretation captions | `figures/`, `figures/figure_captions.md`, `notebooks/03_visualizations.ipynb` |
| **D — Modeling** | Baselines, 10-model leaderboard, rolling-origin validation, ablation study, leakage audit | `reports/D_model_evaluation.md`, `models/final_model.joblib`, `notebooks/04_modeling_and_evaluation.ipynb` |
| **E — Deployed Demo** | Multi-page Streamlit application with test fortnight forecasts & live What-If scenario engine | `app/app.py`, `app/assets/` |
<<<<<<< HEAD
| **F — Slides** | 5-slide deck covering problem, cleaning, findings, modeling, and operational roadmap | `presentation/team_unbearable_slides.pptx`, `presentation/team_unbearable_slides.pdf` |
=======
| **F — Slides** | 5-slide hackathon presentation deck, interactive web viewer, and prompt | `presentation/team_unbearable_slides.pptx`, `presentation/team_unbearable_deck.html`, `presentation/team_unbearable_deck_prompt.md` |
>>>>>>> 7b6dbf6386ddc7fab4fc8f1a2c81f9cabf215de6
| **G — Structure** | Root configuration, pinned dependencies, reproducibility verification | `README.md`, `requirements.txt` |

---

## 🚀 Quick Start & Execution Order

### 1. Environment Installation
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Notebook Execution Order
To reproduce all data science deliverables from scratch:
1. **`notebooks/01_cleaning_and_integration.ipynb`**: Cleans raw data, aligns clocks to `Africa/Addis_Ababa`, executes safe joins, and exports `master_train.csv` and `master_test.csv`.
2. **`notebooks/02_analysis_report.ipynb`**: Executes the 14 analytical investigations across volume, zones, weather response, and events.
3. **`notebooks/03_visualizations.ipynb`**: Renders and exports `fig01` through `fig12` into `figures/`.
<<<<<<< HEAD
4. **`notebooks/04_modeling_and_evaluation.ipynb`**: Evaluates baseline models, trains CatBoost, performs ablation studies, exports `final_model.joblib`, and creates `submission/team_unbearable_submission.csv`.
=======
4. **`notebooks/04_modeling_and_evaluation.ipynb`**: Evaluates baseline models, trains CatBoost, performs ablation studies, exports `final_model.joblib`, and creates `submission/team_qiyas_ai_submission.csv`.
>>>>>>> 7b6dbf6386ddc7fab4fc8f1a2c81f9cabf215de6

### 3. Command-Line Pipeline Execution
Alternatively, execute via modular Python scripts:
```bash
python src/cleaning.py    # Clean tables and generate dim_zone
python src/features.py    # Compute lags, rolling trends & interactions
python src/train.py       # Train winning CatBoost model on master data
python src/predict.py     # Generate final 4,032 submission predictions
```

### 4. Launch Deployed Forecast Demo (Deliverable E)
Run the application locally on your laptop:
```bash
streamlit run app/app.py
```
*Application opens automatically in your browser at `http://localhost:8501`.*

---

## 🏆 Final Model Performance (Validation Set: 18–31 Oct 2025)

| Metric | Winning Model (CatBoostRegressor) | Seasonal-Naive Baseline | Performance Gain |
| :--- | :---: | :---: | :---: |
| **R² Score** | **73.87%** ($0.7387$) | 47.12% ($0.4712$) | **+56.8% variance explained** |
| **MAE** | **6.9201 trips/hour** | 12.1400 trips/hour | **-43.0% error reduction** |
| **RMSE** | **15.6269** | 22.8500 | **-31.6% penalization reduction** |
| **Training Time** | **8.45 seconds** | N/A | High-throughput retraining |
| **Driver Uncertainty** | **~5 drivers / zone-hour** | ~9 drivers / zone-hour | **Precision fleet dispatch** |

---

## 🔒 Pre-Submission Verification Checklist (Section 6.4)
<<<<<<< HEAD
- [x] **Submission CSV**: `submission/team_unbearable_submission.csv` verified with exactly 4,032 rows, zero nulls, zero negative predictions, pre-filled `row_id` order intact.
=======
- [x] **Submission CSV**: `submission/team_qiyas_ai_submission.csv` verified with exactly 4,032 rows, zero nulls, zero negative predictions, pre-filled `row_id` order intact.
>>>>>>> 7b6dbf6386ddc7fab4fc8f1a2c81f9cabf215de6
- [x] **Visualization Pack**: All 12 figures (`fig01` to `fig12`) exist under exact filenames, with all 12 entries described in `figures/figure_captions.md`.
- [x] **Processed Assets**: `master_train.csv`, `master_test.csv`, and `data_dictionary_master.csv` verified in `data/processed/`.
- [x] **Notebook Execution**: All 4 notebooks run top-to-bottom sequentially in a clean Python 3.10+ environment.
- [x] **Demo Application**: Streamlit platform active and verified at `http://localhost:8501`.
- [x] **Presentation Deck**: 5-slide deck provided in both PowerPoint (`.pptx`) and PDF (`.pdf`) format in `presentation/`.
