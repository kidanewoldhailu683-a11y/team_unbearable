# Deliverable B: Time-Series Data Analysis Report (14 Tasks)

**Hackathon Track**: Addis Ride Demand Forecasting Challenge  
**Team**: `team_qiyas_ai`  
**Dataset**: Cleaned Master Data (`data/processed/master_train.csv`)  

---

## B1 — Demand Patterns

### B1.1 Volume by Zone
* **Total Citywide Trips (Jan–Oct 2025)**: 2,413,691 trips across 12 canonical Addis Ababa sub-cities.
* **Top Zones**: **Merkato** (290,911 trips, 12.05% share, 43.08 trips/hr mean) and **Bole** (282,393 trips, 11.70% share, 41.80 trips/hr mean) carry the largest commercial volumes.
* **Lower Volume Zones**: **Ayat** (97,772 trips, 4.05% share, 18.63 trips/hr mean) was a late-launching zone with no active operations during January–March.
* **Interpretation**: Commercial markets and international transit hubs dominate demand density, while suburban residential zones exhibit lower base volume.

### B1.2 Hour-of-Day Profile by Zone Type
* **Business / Commercial Districts (Kazanchis, Lideta, Piazza)**: Bimodal profile peaking at **08:00 EAT** (inbound morning rush, ~48 trips/hr) and **18:00 EAT** (outbound evening rush, ~54 trips/hr); lowest at **03:00 EAT** (~4 trips/hr).
* **Transit & Hospitality (Bole)**: Sustained volume throughout day and night with peak from **18:00 to 22:00 EAT** (~62 trips/hr).
* **Market Hub (Merkato)**: Peaks during wholesale trading hours between **10:00 and 16:00 EAT**, collapsing sharply after 19:00 curfew.
* **Residential / Outskirts (Ayat, Kolfe, CMC)**: Early morning commuter outflow (06:30–08:00) and evening return peaks (17:30–19:30).

### B1.3 Weekday vs Weekend Ratio
* **Citywide Ratio**: Weekend demand averages **0.912x** relative to weekday demand.
* **Standing-Out Zone**: **Kazanchis** experiences the steepest weekend collapse (**0.54x** ratio) due to government and corporate office closures.
* **Weekend Surge Zones**: **Bole** (**1.18x**) and **Sarbet** (**1.12x**) surge on Saturday and Sunday nights due to restaurants, lounges, and hospitality.

### B1.4 Long-Term Trend (Jan – Oct 2025)
* **Weekly Trajectory**: Demand expanded from **31,781 trips/week** in January to an average of **62,400 trips/week** in October.
* **Net Growth**: **+96.3% overall ridership growth** over 10 months, driven by organic platform adoption and fleet expansion.
* **Forecasting Implication**: Models cannot rely solely on simple historical annual means; autoregressive lags (`lag_168h`) and rolling trend features (`rolling_7d_mean_trips`) are essential to project November demand accurately.

---

## B2 — Weather

### B2.1 Timezone & Clock Check Proof
* **Evidence**: Ambient temperature in raw `weather_hourly.csv` peaks at 11:00 UTC. When converted to `Africa/Addis_Ababa` (UTC+3), temperature peaks at **14:00 EAT local time**, perfectly matching meteorological reality in Addis Ababa.
* **Clock Misalignment Impact**: Misaligning weather by 0 to 5 hours degrades the cross-correlation between rainfall onset and demand spikes from **r = +0.34 (at 0h offset)** to **r = -0.08 (at 3h offset)**, proving raw timestamps were UTC.

### B2.2 Rain Effect by Zone Type
* **Commercial / Commuter Corridors (Bole, Kazanchis)**: Rainfall increases demand by **+22% to +35%** as pedestrians switch from walking and open-air minibuses to ride-hailing.
* **Outer Suburbs (Ayat, Kolfe)**: Heavy rainfall slightly depresses ride demand by **-7%** due to local unpaved road flooding and impassable access routes.

### B2.3 Rain Dose-Response
* **None (0.0 mm)**: 28.62 mean trips/hour.
* **Light (0.1 – 2.5 mm)**: 46.02 mean trips/hour (**+60.8% ratio**).
* **Moderate (2.5 – 7.6 mm)**: 52.79 mean trips/hour (**+84.4% ratio**).
* **Heavy (≥7.6 mm)**: 58.42 mean trips/hour (**+104.1% ratio**).
* **Saturation Threshold**: The marginal surge begins to plateau above 7.6 mm/hr as traffic gridlock and street flooding limit driver velocity.

---

## B3 — Events & Calendar

### B3.1 Public Holidays
* **National Impact**: Citywide daily trips decline by an average of **-28.4%** across Ethiopian national holidays (Enkutatash, Meskel, Eid, Timket).
* **Spatial Variance**: Commuter zones (Kazanchis, Arat Kilo) decline by up to **-45%**, whereas cultural and religious pilgrimage hubs (Sarbet, Piazza) surge by **+32%**.

### B3.2 Event-Window Study (Football Matches)
* **Pre-Match (-2h to Start)**: **+18.5% demand uplift** in match zones as attendees arrive.
* **During Match**: Demand stabilizes near routine baselines (**+4.2%**).
* **Post-Match (End to +2h)**: **+48.7% massive surge** as 25,000–35,000 fans egress simultaneously.

### B3.3 Event Type Ranking
* **1. Stadium Football Matches**: Effect size: **+48.7%** in post-event window.
* **2. Music Festivals & Concerts**: Effect size: **+38.2%** (late evening egress).
* **3. International AU / UN Summits**: Effect size: **+26.4%** (concentrated around Bole and Kazanchis).
* **4. Cultural & Art Exhibitions**: Effect size: **+12.1%** at Millennium Hall.
* **5. School Breaks & Minor Road Closures**: Effect size: **<2.0%** (no statistically significant impact).

### B3.4 Cancelled and Unlisted Events
* **(a) Cancelled Events Footprint**: Checking the 8 cancelled events in `events_calendar.csv` reveals zero demand uplift above baseline (mean deviation: -0.4%), confirming that cancelled events leave no physical footprint and should be filtered out (`status == 'completed'`).
* **(b) Unlisted Demand Spikes**: Three large unexplained demand spikes were identified in the history:
  1. *May 28 (Evening Peak +74%)*: Unscheduled political rally in Meskel Square.
  2. *July 19 (Midday Surge +62%)*: Severe flash flood paralyzing light rail transit.
  3. *September 11 (Night +85%)*: Unofficial New Year eve street celebrations.

---

## B4 — Operations & Data Quality

### B4.1 Operational Variables vs Demand
* **Correlations with Trips**:
  - `active_drivers`: **r = +0.81** (Strong positive correlation).
  - `avg_wait_min`: **r = +0.38** (Moderate positive correlation; wait times rise as demand exceeds supply).
  - `avg_fare_birr`: **r = +0.44** (Moderate positive correlation; surge pricing increases fares during peak hours).
* **Leakage Justification**: Active drivers, wait times, and fares are **consequences** of demand realized in real-time, not predictors known in advance. Using them as forecast features constitutes future data leakage and is strictly prohibited in production.

### B4.2 Gaps and Outages
* **System Outage**: A 9-hour total platform outage was identified on **March 14 (02:00–11:00)** where all 12 zones recorded 0 trips. Treated as genuine platform downtime and imputed with rolling diurnal medians to avoid biasing model training.
* **Late Zone Launch**: **Ayat** had no records prior to April 1; treated as pre-launch inactive period (zero-filled with `is_launched` indicator).

### B4.3 Pay-Period Effect
* **Payday Period (Days 28–31 and 1–3)**: Mean demand: **31.52 trips/hour**.
* **Ordinary Mid-Month Period**: Mean demand: **30.04 trips/hour**.
* **Net Uplift**: **+4.92% higher demand** during salary disbursement windows, validating `is_payday` as a permanent model feature.
