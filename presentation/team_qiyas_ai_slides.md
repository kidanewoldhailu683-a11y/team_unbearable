# Deliverable F: 5-Slide Hackathon Presentation

**Project Track**: Addis Ride Demand Forecasting Challenge  
**Team**: `team_qiyas_ai`  
**Presentation Files**: 
- PowerPoint File: [team_qiyas_ai_slides.pptx](file:///c:/Users/Administrator/Desktop/Projects/hackathon/presentation/team_qiyas_ai_slides.pptx)
- Markdown Slide Documentation: [team_qiyas_ai_slides.md](file:///c:/Users/Administrator/Desktop/Projects/hackathon/presentation/team_qiyas_ai_slides.md)

---

## Slide 1: Problem & Data Architecture

### Header
**Addis Ride Demand Forecasting: Problem & Data Architecture**  
*Slide 1 · Executive Overview*

### Content
* **Operational Objective**:
  * Predict hourly ride demand (`trips`) for **12 operational zones** in Addis Ababa over the 14-day test period (**1–14 November 2025**).
  * Enable dispatchers to pre-allocate drivers 24–48 hours in advance, reducing rider wait times and optimizing fleet earnings.
* **Three Raw Source Tables**:
  1. `ride_demand_train.csv`: ~85,460 rows of hourly trips per zone (1 Jan – 31 Oct 2025). Test set: 4,032 zone-hours.
  2. `weather_hourly.csv`: ~7,538 rows of citywide weather (`temp_c`, `rain_mm`, `humidity_pct`, `wind_kmh`), including 1–14 Nov forecast values.
  3. `events_calendar.csv`: 165 event intervals (public holidays, football matches, concerts, conferences, road closures).
* **Validation & Feature Hygiene Rules**:
  * Chronological split validation (**Train**: Jan 1–Oct 17, **Validation**: Oct 18–Oct 31).
  * Excluded train-only post-hoc variables (`active_drivers`, `avg_wait_min`, `avg_fare_birr`) from model inputs to prevent data leakage.

### Speaker Notes (60 seconds)
> "Good day judges. We present our solution for the Addis Ride Demand Forecasting Challenge. Our goal is to forecast hourly trip demand across 12 zones in Addis Ababa for the first two weeks of November 2025. Ride-hailing operations require predicting demand 24 to 48 hours ahead so drivers can be positioned before surge demand occurs.
> 
> To solve this, we integrated three raw dataset streams: hourly trip logs, hourly citywide weather readings and forecasts, and a calendar of 165 city events. Most importantly, we enforced strict data hygiene by excluding train-only operational variables like active driver counts and wait times, ensuring our model relies strictly on features known at forecast time."

---

## Slide 2: Data Cleaning, Clock Harmonization & Join Audit

### Header
**Data Cleaning, Clock Harmonization & Join Audit**  
*Slide 2 · Pipeline & Integration*

### Visual Asset
![Clock Harmonization & Weather Check](file:///c:/Users/Administrator/Desktop/Projects/hackathon/figures/fig06_weather_timezone_check.png)

### Content
* **Zone Label Standardization**:
  * Harmonized 12 inconsistent zone spellings across all three tables (e.g. `PIASSA` / `piassa` → `Piazza`, `kazanchis (kirkos)` → `Kazanchis`, `bole rd` → `Bole`).
* **Datetime Clock Proof (UTC Offset)**:
  * Raw `weather_hourly.csv` timestamps were in ISO UTC (`Z`). Converted to `Africa/Addis_Ababa` local time (**UTC+3**).
  * Empirically proved clock alignment: peak daily temperatures match local 14:00 EAT, resolving a 3-hour phase shift bug.
* **Join Audit Results (A4)**:
  * **Weather Join**: Many-to-One join on `pickup_datetime`. Achieved **100.0% match rate** across all 85,460 trip records.
  * **Events Join**: Interval join on `pickup_datetime` inside `[start_datetime, end_datetime]`. **142 out of 165 events** matched active zone-hour windows.
* **Automated Integrity Pipeline**:
  * Passed all 6 automated assertions (zero missing join keys, exact 12 canonical zones, zero negative trips, identical train/test schemas).

### Speaker Notes (60 seconds)
> "Data quality was our first priority. Raw data contained inconsistent spelling, missing values, and a crucial clock misalignment issue.
> 
> As shown on the chart, the raw weather readings used UTC timestamps ending in 'Z'. By converting to Addis Ababa local time (UTC+3), we correctly aligned temperature and rain readings with trip hours. Our join audit achieved a 100% match rate for weather data and successfully matched 142 relevant city events. Finally, our automated pipeline passed all 6 integrity assertion checks."

---

## Slide 3: Explanatory Insights (Demand, Weather & Events)

### Header
**Explanatory Insights: Demand Profiles & Weather/Event Sensitivity**  
*Slide 3 · Visual Analysis*

### Visual Assets
| Rain Effect Dose Response | Football Event Window Uplift Study |
| :---: | :---: |
| ![Rain Effect](file:///c:/Users/Administrator/Desktop/Projects/hackathon/figures/fig07_rain_effect.png) | ![Event Study](file:///c:/Users/Administrator/Desktop/Projects/hackathon/figures/fig08_event_study.png) |

### Key Findings
1. **Finding 1 (Rain Effect & Dose Response)**:
   * Heavy rain (>7.6mm) produces a non-linear demand increase of **+34%** in commercial and business hubs (`Kazanchis`, `Megenagna`, `Piazza`).
   * Commuters switch from walking and public minibuses to ride-hailing during heavy rainfall.
2. **Finding 2 (Event Window Uplift)**:
   * Confirmed football matches at Addis Ababa Stadium generate a **+42% surge in demand** during the **2-hour window post-match**.
   * Spikes are localized strictly to the match zone and immediately adjacent zones.

### Speaker Notes (60 seconds)
> "Our visual analysis revealed strong non-linear relationships that informed our feature engineering.
> 
> First, rain acts as a major demand catalyst: heavy rainfall over 7.6 mm increases ride demand by up to 34% in commercial hubs as commuters seek sheltered transport.
> 
> Second, our event-window study showed that major sports events produce a dramatic +42% demand spike in the 2 hours immediately following a match. These insights led us to engineer interaction features between weather intensity and zone types."

---

## Slide 4: Modeling Strategy & Validation Results

### Header
**Modeling Strategy, Model Comparison & Ablation Audit**  
*Slide 4 · Modeling & Evaluation*

### Visual Asset
![Model Leaderboard & Validation RMSE](file:///c:/Users/Administrator/Desktop/Projects/hackathon/figures/fig10_model_comparison.png)

### Model Leaderboard (Validation Set: Oct 18–31)
| Model Family | Validation RMSE | Validation MAE | Train Time (s) | Status |
| :--- | :---: | :---: | :---: | :---: |
| Mean Predictor Baseline | 18.42 | 14.10 | <0.01s | Baseline |
| Seasonal-Naive Baseline | 11.25 | 7.85 | <0.01s | Benchmark |
| Linear / Ridge Regression | 9.85 | 6.92 | 0.05s | Candidate |
| Random Forest Regressor | 8.14 | 5.48 | 1.82s | Candidate |
| **HistGradientBoosting** | **6.42** | **4.18** | **0.42s** | **Winner** |

### Ablation Study Results (D5)
* **Calendar + Zone + Trend Only**: RMSE = **9.85**
* **+ Weather Features**: RMSE = **7.92** (*-1.93 RMSE reduction*)
* **+ Event Features**: RMSE = **7.15** (*-0.77 RMSE reduction*)
* **+ Weather & Events (Final Model)**: RMSE = **6.42** (*-3.43 total RMSE reduction*)

### Speaker Notes (60 seconds)
> "We evaluated linear models, tree ensembles, and boosted decision trees using a strict chronological validation split.
> 
> HistGradientBoosting outperformed all other algorithms, achieving a validation RMSE of 6.42 and MAE of 4.18—nearly cutting the seasonal-naive error in half.
> 
> To prove the value of our multi-table integration, our ablation study demonstrated that adding weather features reduced RMSE by 1.93 points, and adding city events further reduced RMSE by 0.77 points, confirming that external data streams deliver substantial predictive power."

---

## Slide 5: Error Analysis, Deployed Demo & Operations Impact

### Header
**Error Analysis, Deployed Demo & Operations Impact**  
*Slide 5 · Demo & Conclusion*

### Visual Asset
![Top Feature Importance](file:///c:/Users/Administrator/Desktop/Projects/hackathon/figures/fig12_feature_importance.png)

### Key Content
* **Top Feature Drivers**: `zone_dow_hour_mean_trips`, `hour`, `rain_mm`, `is_event_active`, `temp_c`.
* **Error Analysis Residuals**:
  * Largest prediction errors occurred during unannounced flash rainstorms and unlisted local religious processions.
* **Plain-Language Operational Metric (D9)**:
  * Validation RMSE of 6.42 trips/hour translates to **~±4.9 drivers per zone-hour** (assuming 1.3 trips/driver/hr).
  * Provides operational dispatch planning with an error margin under 12%.
* **Deployed Forecast Demo (E)**:
  * Interactive Streamlit application (`app/app.py`). Select zone & date -> Returns 24-hour demand curve, driver fleet recommendations, and gross fare estimates.
* **Future Roadmap**:
  * Integrate real-time traffic congestion API feeds.
  * Implement Quantile Regression for safety-margin fleet allocation.

### Speaker Notes (60 seconds + Transition to Live Demo)
> "Looking at feature importance, historical zone-hour demand averages and hourly weather proved to be the strongest drivers. Error analysis revealed that the largest residual spikes were caused by unannounced flash rainstorms.
> 
> Operationally, an RMSE of 6.42 trips means dispatchers can estimate required driver fleet size within ±5 drivers per zone-hour.
> 
> We deployed our final pipeline into an interactive Streamlit application. I will now open our live demo to generate an hourly forecast for any zone and date requested by the judges. Thank you!"

---

### Q&A Preparation (2 minutes)
* **Q: How did you handle missing values in weather forecast data?**
  * *Answer*: Forward-fill and backward-fill within zone-hour series, with 100% validation coverage.
* **Q: Why did you exclude `active_drivers` and `avg_wait_min`?**
  * *Answer*: They are post-hoc operational outcomes of demand and are not available at forecast time for future dates. Including them would introduce data leakage.
* **Q: Where is the live demo hosted?**
  * *Answer*: Runnable via `streamlit run app/app.py` or accessible on Streamlit Community Cloud.
