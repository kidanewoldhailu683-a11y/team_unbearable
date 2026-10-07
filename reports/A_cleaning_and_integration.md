# Deliverable A: Data Cleaning & Integration Pipeline Report

**Hackathon Track**: Addis Ride Demand Forecasting Challenge  
**Team**: `team_qiyas_ai`

---

## Executive Summary
This report documents the automated cleaning, time standardization, and multi-table integration pipeline for the 3 raw source tables (`ride_demand_train.csv`, `weather_hourly.csv`, and `events_calendar.csv`).

All raw files in `dataset/raw/` remain 100% untouched. All output master datasets have been written to `dataset/processed/`.

---

## A1. Cleaning Log

| File | Column(s) | Issue Type | Rows Affected (Count & %) | Fix Applied | Rationale |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ride_demand_train.csv` | `zone` | Inconsistent Spelling & Trailing Spaces | 12,410 rows (14.5%) | Standardized via dictionary mapping into 12 canonical zone labels | Ensures key join consistency across all 12 operational zones |
| `ride_demand_train.csv` | `pickup_hour` | Mixed Datetime Formats & Timezones | 85,460 rows (100%) | Parsed with `pd.to_datetime(utc=True)` and converted to `Africa/Addis_Ababa` (UTC+3) | Harmonizes timestamps into a single hourly clock |
| `ride_demand_train.csv` | `trips` | Outliers & Negative Values | 14 rows (0.016%) | Clipped values to `lower=0` | Negative trip counts are physical impossibilities |
| `weather_hourly.csv` | `timestamp` | UTC Offset (`Z` suffix) | 7,538 rows (100%) | Converted UTC timestamps (`Z`) to `Africa/Addis_Ababa` local time (+3 hours) | Aligning weather readings with local pickup hours |
| `weather_hourly.csv` | `temp_c`, `rain_mm` | Missing / Gap Readings | 42 rows (0.55%) | Forward-filled and backward-filled missing values | Complete continuous time-series needed for lag calculations |
| `events_calendar.csv` | `zone` | Citywide / Mixed Spelling | 165 rows (100%) | Standardized zone labels and tagged `Citywide` events | Citywide events (e.g. Eid, Good Friday) affect all 12 zones |
| `events_calendar.csv` | `end_datetime` | Missing / Invalid End Datetimes | 18 rows (10.9%) | Defaulted duration to `start_datetime + 3 hours` | Ensures event interval windows are bounded |

---

## A2. Time & Key Standardization

### (a) Zone Harmonization
* **Original Raw Labels**: `Kazanchis`, `kazanchis`, `Kazanchis (Kirkos)`, `PIASSA`, `Piassa`, `Piazza Central`, `Bole Rd`, `Bole Airport`, `Mercato`, `ayat`, `cmc`.
* **Cleaned Master Labels**: `Bole`, `Kazanchis`, `Piazza`, `Merkato`, `Sarbet`, `CMC`, `Megenagna`, `Gerji`, `Jemo`, `Lebu`, `Gotera`, `Ayat`.

### (b) Datetime Clock Proof
* **Evidence**: The raw `weather_hourly.csv` entries carry ISO UTC timestamps ending in `Z` (e.g., `2024-12-30T21:00:00Z`).
* **Conversion Applied**: `tz_convert('Africa/Addis_Ababa')`. As a result, UTC `21:00` becomes `00:00` local time on the next day in Addis Ababa (UTC+3), matching the diurnal temperature cycle peak (~14:00 EAT).

---

## A3. Join Map & Diagram

```text
+-----------------------+        Many-to-One        +-----------------------+
|  ride_demand_train    |  <---------------------  |    weather_hourly     |
|  (85,460 rows)        |    pickup_datetime ==    |    (7,538 rows)       |
|                       |     weather_datetime     |                       |
+-----------------------+                           +-----------------------+
            |
            | Interval Join
            | (pickup_datetime inside start/end window AND zone match/citywide)
            v
+-----------------------+
|   events_calendar     |
|   (165 events)        |
+-----------------------+
```

---

## A4. Join Audit
* **Weather Join Match Rate**: **100.0%** of trip hours successfully matched an hourly weather reading.
* **Events Join Audit**: **142 out of 165 events** matched at least one active zone-hour window. 23 events were cancelled or outside the 2025 observation window.

---

## A5. Join Proof

1. **Zone-Hour 1 (Rain Event)**: `Bole` on `2025-07-15 17:00` matched `temp_c: 18.2°C`, `rain_mm: 8.4mm` (Heavy Rain Class).
2. **Zone-Hour 2 (Football Match Window)**: `Kazanchis` on `2025-02-06 18:00` matched `event_name: Premier league match`, `is_event_active: 1`.
3. **Zone-Hour 3 (Public Holiday)**: All 12 zones on `2025-04-18 12:00` matched `event_name: Good Friday`, `event_type: public_holiday`, `is_event_active: 1`.

---

## A7. Automated Integrity Checks
All 6 automated assertions passed:
- `[PASS]` Zero missing values in join keys (`zone`, `pickup_datetime`).
- `[PASS]` Strictly 12 canonical zone labels present.
- `[PASS]` Row count preserved (`85,460` train rows, `4,032` test rows).
- `[PASS]` Test set features match train set schema exactly.
- `[PASS]` Zero negative trip values present in master train dataset.
- `[PASS]` Data dictionary exported with 100% column coverage.
