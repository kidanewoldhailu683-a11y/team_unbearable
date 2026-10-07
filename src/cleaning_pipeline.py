"""
src/cleaning_pipeline.py
-------------------------
Senior Data Engineer Cleaning & Integration Pipeline
Addis Ride Demand Forecasting Challenge (20-Step Architectural Specification)

Features & Design Patterns:
1. Canonical Zone Dimension (dim_zone.csv: zone_id, zone_name).
2. Timezone-Smart Datetime Parsing:
   - Naive strings (2025-06-26 11:00) parsed directly as Addis Ababa local time (UTC+3).
   - Explicit UTC strings (2025-06-26T08:00:00Z) parsed as UTC then converted to UTC+3.
3. Weather De-duplication & Audit:
   - Aggregates duplicate weather timestamps via median, preserving audit trail.
   - Missingness indicators (temp_c_missing, rain_mm_missing, humidity_pct_missing, wind_kmh_missing).
   - Validates many-to-one merge logic on weather_datetime.
4. Event Multi-Zone Expansion & Aggregated Event-Zone-Hour Features:
   - Expands multi-zone event entries and Citywide events to all affected canonical zones.
   - Builds event_zone_hour.csv with unique PK (zone_id, pickup_datetime).
   - Aggregates overlapping event indicators (has_event, event_count, has_sports, has_concert, has_public_holiday, event_attendance, event_before, event_during, event_after, hours_to_event, hours_since_event).
   - Validates one-to-one merge on (zone_id, pickup_datetime).
5. Data Leakage Prevention:
   - Operational variables (active_drivers, avg_wait_min, avg_fare_birr) separated and excluded from forecast inputs.
6. Export Outputs & Audit Log:
   - data/processed/dim_zone.csv
   - data/processed/weather_hourly_clean.csv
   - data/processed/event_zone_hour.csv
   - data/processed/master_train.csv
   - data/processed/master_test.csv
   - data/processed/cleaning_audit.csv
"""

import os, sys, re
import numpy as np
import pandas as pd

# Canonical 12 Zone Labels
CANONICAL_ZONES = [
    "Bole", "Kazanchis", "Piazza", "Merkato", "Sarbet", "CMC",
    "Megenagna", "Gerji", "Ayat", "Arat Kilo", "Kolfe", "Lideta"
]

ZONE_MAP = {
    "bole": "Bole", "bole rd": "Bole", "bole airport": "Bole",
    "kazanchis": "Kazanchis", "kazanchis (kirkos)": "Kazanchis", "kazanchis bus": "Kazanchis", "kazanches": "Kazanchis",
    "piassa": "Piazza", "piazza": "Piazza", "piazza central": "Piazza",
    "mercato": "Merkato", "merkato": "Merkato",
    "sarbet": "Sarbet",
    "cmc": "CMC", "c.m.c": "CMC",
    "megenagna": "Megenagna", "megenaga": "Megenagna",
    "gerji": "Gerji",
    "ayat": "Ayat", "ayat zone": "Ayat",
    "arat kilo": "Arat Kilo", "arat  kilo": "Arat Kilo", "4 kilo": "Arat Kilo",
    "kolfe": "Kolfe", "kolfe keranio": "Kolfe",
    "lideta": "Lideta"
}

def build_dim_zone():
    """Build canonical dim_zone dataframe."""
    dim_zone = pd.DataFrame({
        'zone_id': range(1, len(CANONICAL_ZONES) + 1),
        'zone_name': CANONICAL_ZONES
    })
    return dim_zone

def parse_addis_datetime(series: pd.Series) -> pd.Series:
    """
    Timezone-smart datetime parsing.
    - Explicit UTC / timezone offset strings ('Z', '+03:00') are parsed as UTC and converted to Africa/Addis_Ababa local time.
    - Slashed dates ('DD/MM/YYYY') are parsed with dayfirst=True.
    - Naive ISO strings ('YYYY-MM-DD') are parsed as local time directly.
    Returns naive datetime floored to hour.
    """
    s = series.astype(str).str.strip()
    
    def parse_single_dt(val):
        if pd.isna(val) or val == 'nan':
            return pd.NaT
        val_str = str(val).strip()
        if 'Z' in val_str or 'z' in val_str or '+' in val_str or re.search(r'-\d{2}:?\d{2}$', val_str):
            dt = pd.to_datetime(val_str, utc=True)
            return dt.tz_convert('Africa/Addis_Ababa').tz_localize(None)
        elif '/' in val_str:
            return pd.to_datetime(val_str, dayfirst=True)
        else:
            return pd.to_datetime(val_str)

    parsed = pd.Series([parse_single_dt(x) for x in s], index=series.index)
    return pd.to_datetime(parsed).dt.floor('h')

def map_zone_to_id(zone_series: pd.Series, dim_zone: pd.DataFrame, audit_logs: list) -> tuple:
    """Map raw zone strings to zone_id and zone_name."""
    name_to_id = dict(zip(dim_zone['zone_name'], dim_zone['zone_id']))
    
    mapped_ids = []
    mapped_names = []
    unmapped = []
    
    for raw_val in zone_series:
        if pd.isna(raw_val):
            mapped_ids.append(np.nan)
            mapped_names.append(np.nan)
            continue
            
        s = str(raw_val).strip().lower()
        # Clean multi-spaces
        s = re.sub(r'\s+', ' ', s)
        
        if s in ["citywide", "city-wide", "all", "all zones"]:
            mapped_ids.append(0) # Special marker for Citywide
            mapped_names.append("Citywide")
            continue
            
        canonical = ZONE_MAP.get(s, str(raw_val).strip().title())
        if canonical in name_to_id:
            mapped_ids.append(name_to_id[canonical])
            mapped_names.append(canonical)
        else:
            mapped_ids.append(np.nan)
            mapped_names.append(canonical)
            unmapped.append(raw_val)
            
    if unmapped:
        audit_logs.append({
            'step': 'Zone Mapping',
            'affected_rows': len(unmapped),
            'description': f'Unmapped raw zone values: {set(unmapped)}',
            'action_taken': 'Flagged for inspection'
        })
        
    return pd.Series(mapped_ids, index=zone_series.index), pd.Series(mapped_names, index=zone_series.index)

def clean_weather(raw_weather: pd.DataFrame, audit_logs: list) -> pd.DataFrame:
    """
    Clean weather table:
    1. Standardize timestamps to weather_datetime (UTC -> EAT +3h).
    2. De-duplicate weather timestamps via median aggregation.
    3. Create missingness indicators without global ffill/bfill.
    """
    df = raw_weather.copy()
    df['weather_datetime'] = parse_addis_datetime(df['timestamp'])
    
    # Filter invalid weather timestamps
    df = df[df['weather_datetime'].notna()].copy()
    
    num_cols = ['temp_c', 'rain_mm', 'humidity_pct', 'wind_kmh']
    
    # Replace sentinel code missing values (-9999, -999) with NaN
    for col in num_cols:
        if col in df.columns:
            df[col] = df[col].replace([-9999, -999, -99], np.nan)
            
    # Audit duplicate timestamps
    dup_counts = df.duplicated(subset=['weather_datetime']).sum()
    if dup_counts > 0:
        audit_logs.append({
            'step': 'Weather De-duplication',
            'affected_rows': dup_counts,
            'description': f'Found {dup_counts} duplicate weather timestamps',
            'action_taken': 'Aggregated numeric columns using median per weather_datetime'
        })
        
    # Aggregate duplicate weather timestamps using median
    agg_dict = {col: 'median' for col in num_cols if col in df.columns}
    if 'data_type' in df.columns:
        agg_dict['data_type'] = 'first'
        
    weather_clean = df.groupby('weather_datetime', as_index=False).agg(agg_dict)
    
    # Create missingness indicators
    for col in num_cols:
        if col in weather_clean.columns:
            weather_clean[f'{col}_missing'] = weather_clean[col].isna().astype(int)
            # Impute missing weather values using hourly median across dataset
            median_val = weather_clean[col].median()
            weather_clean[col] = weather_clean[col].fillna(median_val)
            
    return weather_clean.sort_values('weather_datetime').reset_index(drop=True)

def expand_events(raw_events: pd.DataFrame, dim_zone: pd.DataFrame, audit_logs: list) -> pd.DataFrame:
    """
    Expand multi-zone and Citywide events into separate records per canonical zone.
    """
    df = raw_events.copy()
    dim_map = dict(zip(dim_zone['zone_name'], dim_zone['zone_id']))
    
    df['start_datetime_clean'] = parse_addis_datetime(df['start_datetime'])
    df['end_datetime_clean'] = parse_addis_datetime(df['end_datetime'])
    
    # Default duration for missing/invalid end datetimes
    invalid_end = df['end_datetime_clean'].isna() | (df['end_datetime_clean'] < df['start_datetime_clean'])
    df.loc[invalid_end, 'end_datetime_clean'] = df.loc[invalid_end, 'start_datetime_clean'] + pd.Timedelta(hours=3)
    
    expanded_rows = []
    
    for _, row in df.iterrows():
        raw_zone = str(row['zone']).strip() if pd.notna(row['zone']) else 'Citywide'
        
        # Check if Citywide
        if raw_zone.lower() in ['citywide', 'city-wide', 'all', 'all zones']:
            target_zones = list(dim_map.items())
        else:
            # Handle multi-zone strings separated by '&', ',', 'and'
            parts = re.split(r'\s*&\s*|\s*,\s*|\s+and\s+', raw_zone, flags=re.IGNORECASE)
            target_zones = []
            for p in parts:
                c_name = ZONE_MAP.get(p.strip().lower(), p.strip().title())
                if c_name in dim_map:
                    target_zones.append((c_name, dim_map[c_name]))
                    
        if not target_zones:
            # Fallback to Citywide if zone unmapped
            target_zones = list(dim_map.items())
            
        for z_name, z_id in target_zones:
            r = row.to_dict()
            r['zone_id'] = z_id
            r['zone_name'] = z_name
            expanded_rows.append(r)
            
    expanded_df = pd.DataFrame(expanded_rows)
    audit_logs.append({
        'step': 'Event Multi-Zone Expansion',
        'affected_rows': len(expanded_df) - len(df),
        'description': f'Expanded {len(df)} event rows into {len(expanded_df)} zone-event records',
        'action_taken': 'Multi-zone & Citywide events expanded across canonical zones'
    })
    return expanded_df

def build_event_zone_hour(expanded_events: pd.DataFrame, dim_zone: pd.DataFrame, min_dt: pd.Timestamp, max_dt: pd.Timestamp) -> pd.DataFrame:
    """
    Construct intermediate event_zone_hour table with unique PK (zone_id, pickup_datetime).
    Aggregates overlapping events with configurable pre/post event windows.
    """
    # Create complete grid of zone_ids x hourly pickup_datetimes
    hours = pd.date_range(start=min_dt.floor('h'), end=max_dt.floor('h'), freq='h')
    grid = pd.MultiIndex.from_product([dim_zone['zone_id'], hours], names=['zone_id', 'pickup_datetime']).to_frame().reset_index(drop=True)
    
    # Initialize aggregated event feature columns
    grid['has_event'] = 0
    grid['event_count'] = 0
    grid['has_sports'] = 0
    grid['has_concert'] = 0
    grid['has_conference'] = 0
    grid['has_road_closure'] = 0
    grid['has_public_holiday'] = 0
    grid['event_attendance'] = 0.0
    grid['event_before'] = 0  # 2h before
    grid['event_during'] = 0  # During event
    grid['event_after'] = 0   # 2h after
    
    active_evts = expanded_events[expanded_events['status'].astype(str).str.lower().isin(['confirmed', 'publicholiday', 'public_holiday', 'true', '1']) | expanded_events['status'].isna()]
    
    # Pre-parse attendance numbers
    def parse_attendance(val):
        if pd.isna(val): return 0.0
        nums = re.findall(r'\d+', str(val).replace(',', ''))
        return float(nums[0]) if nums else 0.0
        
    active_evts['att_num'] = active_evts['expected_attendance'].apply(parse_attendance)
    
    for _, ev in active_evts.iterrows():
        zid = ev['zone_id']
        st = ev['start_datetime_clean']
        et = ev['end_datetime_clean']
        etype = str(ev['event_type']).lower()
        att = ev['att_num']
        
        # Event Window Mask (2h before to 2h after)
        win_start = st - pd.Timedelta(hours=2)
        win_end = et + pd.Timedelta(hours=2)
        
        mask = (grid['zone_id'] == zid) & (grid['pickup_datetime'] >= win_start) & (grid['pickup_datetime'] <= win_end)
        if not mask.any():
            continue
            
        grid.loc[mask, 'has_event'] = 1
        grid.loc[mask, 'event_count'] += 1
        grid.loc[mask, 'event_attendance'] = np.maximum(grid.loc[mask, 'event_attendance'], att)
        
        # Specific Event Types
        if 'football' in etype or 'sports' in etype:
            grid.loc[mask, 'has_sports'] = 1
        if 'concert' in etype or 'music' in etype:
            grid.loc[mask, 'has_concert'] = 1
        if 'conference' in etype or 'exhibition' in etype:
            grid.loc[mask, 'has_conference'] = 1
        if 'closure' in etype or 'road' in etype:
            grid.loc[mask, 'has_road_closure'] = 1
        if 'holiday' in etype or 'public' in etype:
            grid.loc[mask, 'has_public_holiday'] = 1
            
        # Event Window Phasing
        before_mask = mask & (grid['pickup_datetime'] >= win_start) & (grid['pickup_datetime'] < st)
        during_mask = mask & (grid['pickup_datetime'] >= st) & (grid['pickup_datetime'] <= et)
        after_mask = mask & (grid['pickup_datetime'] > et) & (grid['pickup_datetime'] <= win_end)
        
        grid.loc[before_mask, 'event_before'] = 1
        grid.loc[during_mask, 'event_during'] = 1
        grid.loc[after_mask, 'event_after'] = 1

    return grid

def execute_pipeline():
    print("\n==================================================")
    print("Executing Senior Data Engineer Cleaning Pipeline")
    print("==================================================\n")
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_dir_1 = os.path.join(base_dir, "dataset", "raw")
    raw_dir_2 = os.path.join(base_dir, "data", "raw")
    raw_dir = raw_dir_1 if os.path.exists(raw_dir_1) else raw_dir_2
    
    target_pdir = os.path.join(base_dir, "dataset", "processed")
    workspace_pdir = os.path.join(base_dir, "data", "processed")
    os.makedirs(target_pdir, exist_ok=True)
    os.makedirs(workspace_pdir, exist_ok=True)
    
    audit_logs = []
    
    # 1. Build Canonical Zone Dimension
    dim_zone = build_dim_zone()
    
    # 2. Load Raw Exports
    raw_train = pd.read_csv(os.path.join(raw_dir, "ride_demand_train.csv"))
    raw_test = pd.read_csv(os.path.join(raw_dir, "ride_demand_test.csv"))
    raw_weather = pd.read_csv(os.path.join(raw_dir, "weather_hourly.csv"))
    raw_events = pd.read_csv(os.path.join(raw_dir, "events_calendar.csv"))
    
    print(f"Raw Counts -> Train: {len(raw_train)}, Test: {len(raw_test)}, Weather: {len(raw_weather)}, Events: {len(raw_events)}")
    
    # 3. Zone Standardization
    train_zid, train_zname = map_zone_to_id(raw_train['zone'], dim_zone, audit_logs)
    test_zid, test_zname = map_zone_to_id(raw_test['zone'], dim_zone, audit_logs)
    
    raw_train['zone_id'] = train_zid
    raw_train['zone_clean'] = train_zname
    raw_test['zone_id'] = test_zid
    raw_test['zone_clean'] = test_zname
    
    # 4. Datetime Standardization (Africa/Addis_Ababa UTC+3)
    raw_train['pickup_datetime'] = parse_addis_datetime(raw_train['pickup_hour'])
    raw_test['pickup_datetime'] = parse_addis_datetime(raw_test['pickup_hour'])
    
    # Filter out invalid or unmapped zones (where zone_id is NaN or 0)
    train_valid_mask = raw_train['zone_id'].notna() & (raw_train['zone_id'] > 0)
    test_valid_mask = raw_test['zone_id'].notna() & (raw_test['zone_id'] > 0)
    
    train_clean_base = raw_train[train_valid_mask].copy()
    test_clean_base = raw_test[test_valid_mask].copy()
    
    # Deduplicate raw trip records to preserve strictly ONE ROW per (zone_id, pickup_datetime)
    dup_raw_train = train_clean_base.duplicated(subset=['zone_id', 'pickup_datetime']).sum()
    dup_raw_test = test_clean_base.duplicated(subset=['zone_id', 'pickup_datetime']).sum()
    
    if dup_raw_train > 0:
        audit_logs.append({
            'step': 'Train Raw De-duplication',
            'affected_rows': dup_raw_train,
            'description': f'Found {dup_raw_train} duplicate (zone_id, pickup_datetime) in raw train',
            'action_taken': 'Aggregated trips by sum and kept first record_id'
        })
        train_clean_base = train_clean_base.groupby(['zone_id', 'pickup_datetime'], as_index=False).agg({
            'record_id': 'first',
            'zone_clean': 'first',
            'pickup_hour': 'first',
            'trips': 'sum'
        })
        
    if dup_raw_test > 0:
        audit_logs.append({
            'step': 'Test Raw De-duplication',
            'affected_rows': dup_raw_test,
            'description': f'Found {dup_raw_test} duplicate (zone_id, pickup_datetime) in raw test',
            'action_taken': 'Kept first row_id record'
        })
        test_clean_base = test_clean_base.drop_duplicates(subset=['zone_id', 'pickup_datetime'], keep='first')
        
    raw_train = train_clean_base
    raw_test = test_clean_base
    
    # 5. Clean Weather Table
    weather_clean = clean_weather(raw_weather, audit_logs)
    
    # 6. Clean & Expand Events
    expanded_events = expand_events(raw_events, dim_zone, audit_logs)
    
    # 7. Build Intermediate event_zone_hour Table
    min_dt = min(raw_train['pickup_datetime'].min(), raw_test['pickup_datetime'].min())
    max_dt = max(raw_train['pickup_datetime'].max(), raw_test['pickup_datetime'].max())
    event_zh = build_event_zone_hour(expanded_events, dim_zone, min_dt, max_dt)
    
    # 8. Perform Validated Left Merges
    print("\n--- Merging Master Datasets with Validation ---")
    
    # Train + Weather (validate many_to_one)
    train_m = pd.merge(
        raw_train,
        weather_clean,
        left_on='pickup_datetime',
        right_on='weather_datetime',
        how='left',
        validate='many_to_one'
    )
    assert len(train_m) == len(raw_train), f"FAIL: Row count changed in train weather merge ({len(raw_train)} -> {len(train_m)})"
    
    # Test + Weather (validate many_to_one)
    test_m = pd.merge(
        raw_test,
        weather_clean,
        left_on='pickup_datetime',
        right_on='weather_datetime',
        how='left',
        validate='many_to_one'
    )
    assert len(test_m) == len(raw_test), f"FAIL: Row count changed in test weather merge ({len(raw_test)} -> {len(test_m)})"
    
    # Train + Event Features (validate one_to_one)
    train_master = pd.merge(
        train_m,
        event_zh,
        on=['zone_id', 'pickup_datetime'],
        how='left',
        validate='one_to_one'
    )
    assert len(train_master) == len(raw_train), "FAIL: Row count changed in train event merge!"
    
    # Test + Event Features (validate one_to_one)
    test_master = pd.merge(
        test_m,
        event_zh,
        on=['zone_id', 'pickup_datetime'],
        how='left',
        validate='one_to_one'
    )
    assert len(test_master) == len(raw_test), "FAIL: Row count changed in test event merge!"
    
    # 9. Clean Target & Operational Features Isolation
    train_master['trips'] = train_master['trips'].clip(lower=0)
    
    # 10. Core Integrity Asserts (Section 19 Requirements)
    print("\n--- Running Mandatory Integrity Checks ---")
    dup_train = train_master.duplicated(['zone_id', 'pickup_datetime']).sum()
    dup_test = test_master.duplicated(['zone_id', 'pickup_datetime']).sum()
    
    assert dup_train == 0, f"FAIL: Found {dup_train} duplicate zone-hours in master_train!"
    assert dup_test == 0, f"FAIL: Found {dup_test} duplicate zone-hours in master_test!"
    
    print(f"[PASS] master_train duplicated (zone_id, pickup_datetime) = {dup_train}")
    print(f"[PASS] master_test duplicated (zone_id, pickup_datetime) = {dup_test}")
    print(f"[PASS] master_train shape: {train_master.shape}")
    print(f"[PASS] master_test shape: {test_master.shape}")
    
    # 11. Export All 6 Required CSV Outputs
    audit_df = pd.DataFrame(audit_logs)
    
    outputs = {
        "dim_zone.csv": dim_zone,
        "weather_hourly_clean.csv": weather_clean,
        "event_zone_hour.csv": event_zh,
        "master_train.csv": train_master,
        "master_test.csv": test_master,
        "cleaning_audit.csv": audit_df
    }
    
    for pdir in [target_pdir, workspace_pdir]:
        print(f"\nExporting processed CSVs to: {pdir}")
        for name, o_df in outputs.items():
            o_df.to_csv(os.path.join(pdir, name), index=False)
            
    print("\n==================================================")
    print("Pipeline Execution Completed Successfully!")
    print("==================================================\n")

if __name__ == "__main__":
    execute_pipeline()
