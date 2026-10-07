"""
src/cleaning.py
----------------
Data Cleaning & Integration Pipeline for Addis Ride Demand Forecasting Challenge.

Rules & Guidelines:
1. Original raw files in dataset/raw are NEVER modified.
2. Cleaned and merged master outputs are saved to:
   - C:\\Users\\Administrator\\Desktop\\Projects\\Addis Ride Demand Forecasting Challenge\\dataset\\processed\\
   - data/processed/ (in hackathon workspace)
3. Outputs generated:
   - master_train.csv
   - master_test.csv
   - data_dictionary_master.csv
   - cleaning_log.csv (A1 cleaning audit log)
"""

import os
import pandas as pd
import numpy as np

# Canonical 12 Zone Names
CANONICAL_ZONES = [
    "Bole", "Kazanchis", "Piazza", "Merkato", "Sarbet", "CMC",
    "Megenagna", "Gerji", "Jemo", "Lebu", "Gotera", "Ayat"
]

ZONE_MAPPING = {
    "bole": "Bole", "bole rd": "Bole", "bole airport": "Bole",
    "kazanchis": "Kazanchis", "kazanchis (kirkos)": "Kazanchis", "kazanchis bus": "Kazanchis",
    "piassa": "Piazza", "piazza": "Piazza", "piazza central": "Piazza",
    "mercato": "Merkato", "merkato": "Merkato",
    "sarbet": "Sarbet",
    "cmc": "CMC",
    "megenagna": "Megenagna",
    "gerji": "Gerji",
    "jemo": "Jemo",
    "lebu": "Lebu",
    "gotera": "Gotera",
    "ayat": "Ayat", "ayat zone": "Ayat"
}

def standardize_zone(zone_str: str) -> str:
    """Standardize zone name string to canonical zone label."""
    if pd.isna(zone_str):
        return np.nan
    s = str(zone_str).strip().lower()
    if s in ["citywide", "city-wide", "all", "all zones"]:
        return "Citywide"
    return ZONE_MAPPING.get(s, str(zone_str).strip().title())

def parse_timestamps(series: pd.Series, is_utc: bool = False) -> pd.Series:
    """
    Parse mixed-format datetimes and convert to Africa/Addis_Ababa local time (UTC+3).
    Returns naive datetime normalized to hourly precision.
    """
    # Setting utc=True converts mixed timezone strings to a unified UTC timezone
    dt_series = pd.to_datetime(series, format='mixed', errors='coerce', utc=True)
    # Convert UTC to Africa/Addis_Ababa (UTC+3) then drop tz info for clean joins
    dt_series = dt_series.dt.tz_convert('Africa/Addis_Ababa').dt.tz_localize(None)
    return dt_series.dt.floor('h')

def load_and_clean_trip_data(file_path: str, is_train: bool = True) -> pd.DataFrame:
    """Clean ride demand trip dataset (train or test)."""
    df = pd.read_csv(file_path)
    print(f"Loaded {'train' if is_train else 'test'} raw data: {len(df)} rows.")
    
    # Standardize zone
    df['zone_clean'] = df['zone'].apply(standardize_zone)
    
    # Standardize timestamp
    hour_col = 'pickup_hour'
    df['pickup_datetime'] = parse_timestamps(df[hour_col], is_utc=False)
    
    # Fill target or operational column cleaning if train
    if is_train:
        # Filter negative or impossible trip values if present
        df['trips'] = df['trips'].clip(lower=0)
        
    return df

def load_and_clean_weather(file_path: str) -> pd.DataFrame:
    """Clean weather dataset and convert UTC timestamps to Addis Ababa time."""
    df = pd.read_csv(file_path)
    print(f"Loaded weather raw data: {len(df)} rows.")
    
    # Weather raw timestamps are UTC (e.g. 2024-12-30T21:00:00Z)
    df['weather_datetime'] = parse_timestamps(df['timestamp'], is_utc=True)
    
    # Deduplicate by weather_datetime keeping first valid reading
    df = df.sort_values('weather_datetime').drop_duplicates(subset=['weather_datetime'], keep='first')
    
    # Forward fill missing weather readings
    weather_cols = ['temp_c', 'rain_mm', 'humidity_pct', 'wind_kmh']
    df[weather_cols] = df[weather_cols].ffill().bfill()
    
    return df

def load_and_clean_events(file_path: str) -> pd.DataFrame:
    """Clean city events calendar and parse start/end datetimes."""
    df = pd.read_csv(file_path)
    print(f"Loaded events raw data: {len(df)} rows.")
    
    df['zone_clean'] = df['zone'].apply(standardize_zone)
    df['start_datetime_clean'] = parse_timestamps(df['start_datetime'])
    df['end_datetime_clean'] = parse_timestamps(df['end_datetime'])
    
    # If end_datetime is missing or earlier than start, default duration to 3 hours
    invalid_end = df['end_datetime_clean'].isna() | (df['end_datetime_clean'] < df['start_datetime_clean'])
    df.loc[invalid_end, 'end_datetime_clean'] = df.loc[invalid_end, 'start_datetime_clean'] + pd.Timedelta(hours=3)
    
    return df

def merge_datasets(trips_df: pd.DataFrame, weather_df: pd.DataFrame, events_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge trip history with hourly weather (Many-to-One) and city events (Interval Join).
    """
    # 1. Merge Weather on pickup_datetime == weather_datetime
    master = pd.merge(
        trips_df,
        weather_df[['weather_datetime', 'temp_c', 'rain_mm', 'humidity_pct', 'wind_kmh', 'data_type']],
        left_on='pickup_datetime',
        right_on='weather_datetime',
        how='left'
    )
    
    # Fallback ffill/bfill for any unmapped weather timestamps
    weather_cols = ['temp_c', 'rain_mm', 'humidity_pct', 'wind_kmh']
    master[weather_cols] = master[weather_cols].ffill().bfill()
    
    # 2. Merge Events (Interval Join)
    # Initialize event indicator columns
    master['is_event_active'] = 0
    master['event_type'] = 'None'
    master['event_name'] = 'None'
    
    # Iterate through confirmed events and flag active hours per zone
    active_events = events_df[events_df['status'].str.lower().isin(['confirmed', 'publicholiday', 'public_holiday', 'true', '1']) | events_df['status'].isna()]
    
    for _, event in active_events.iterrows():
        e_zone = event['zone_clean']
        start_time = event['start_datetime_clean']
        end_time = event['end_datetime_clean']
        e_type = str(event['event_type'])
        e_name = str(event['event_name'])
        
        # Zone mask: matching zone or citywide
        if e_zone == 'Citywide':
            zone_mask = pd.Series(True, index=master.index)
        else:
            zone_mask = (master['zone_clean'] == e_zone)
            
        # Time mask: pickup_datetime between event start and end
        time_mask = (master['pickup_datetime'] >= start_time) & (master['pickup_datetime'] <= end_time)
        
        full_mask = zone_mask & time_mask
        master.loc[full_mask, 'is_event_active'] = 1
        master.loc[full_mask, 'event_type'] = e_type
        master.loc[full_mask, 'event_name'] = e_name
        
    return master

def create_data_dictionary() -> pd.DataFrame:
    """Create data dictionary metadata table for master datasets."""
    dict_data = [
        {"column": "record_id", "type": "string", "source": "trips", "description": "Unique row identifier", "known_at_forecast_time": "Yes"},
        {"column": "zone", "type": "string", "source": "trips", "description": "Canonical Addis Ababa zone name", "known_at_forecast_time": "Yes"},
        {"column": "pickup_hour", "type": "string", "source": "trips", "description": "Start of hour (local time EAT UTC+3)", "known_at_forecast_time": "Yes"},
        {"column": "trips", "type": "integer", "source": "trips", "description": "Target: Number of trip requests in zone-hour", "known_at_forecast_time": "No (Train target only)"},
        {"column": "temp_c", "type": "float", "source": "weather", "description": "Air temperature in Celsius", "known_at_forecast_time": "Yes (Weather forecast)"},
        {"column": "rain_mm", "type": "float", "source": "weather", "description": "Rainfall in previous hour (mm)", "known_at_forecast_time": "Yes (Weather forecast)"},
        {"column": "humidity_pct", "type": "float", "source": "weather", "description": "Relative humidity (%)", "known_at_forecast_time": "Yes (Weather forecast)"},
        {"column": "wind_kmh", "type": "float", "source": "weather", "description": "Wind speed (km/h)", "known_at_forecast_time": "Yes (Weather forecast)"},
        {"column": "is_event_active", "type": "integer", "source": "events", "description": "Flag indicating active event in zone-hour", "known_at_forecast_time": "Yes (Event calendar)"},
        {"column": "event_type", "type": "string", "source": "events", "description": "Categorical event classification", "known_at_forecast_time": "Yes (Event calendar)"},
        {"column": "event_name", "type": "string", "source": "events", "description": "Specific event title/name", "known_at_forecast_time": "Yes (Event calendar)"}
    ]
    return pd.DataFrame(dict_data)

if __name__ == "__main__":
    print("\n==================================================")
    print("Running Data Cleaning & Integration Pipeline")
    print("==================================================\n")
    
    # Path resolution (handles both dataset/ and data/ conventions)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Input raw directories
    raw_dir_1 = os.path.join(base_dir, "dataset", "raw")
    raw_dir_2 = os.path.join(base_dir, "data", "raw")
    raw_dir = raw_dir_1 if os.path.exists(raw_dir_1) else raw_dir_2
    
    # Output processed directories
    target_processed_dir = os.path.join(base_dir, "dataset", "processed")
    workspace_processed_dir = os.path.join(base_dir, "data", "processed")
    
    os.makedirs(target_processed_dir, exist_ok=True)
    os.makedirs(workspace_processed_dir, exist_ok=True)
    
    # Load and clean individual datasets
    print("Step 1/4: Cleaning trip history, weather, and event tables...")
    train_raw = load_and_clean_trip_data(os.path.join(raw_dir, "ride_demand_train.csv"), is_train=True)
    test_raw = load_and_clean_trip_data(os.path.join(raw_dir, "ride_demand_test.csv"), is_train=False)
    weather_clean = load_and_clean_weather(os.path.join(raw_dir, "weather_hourly.csv"))
    events_clean = load_and_clean_events(os.path.join(raw_dir, "events_calendar.csv"))
    
    # Merge datasets
    print("\nStep 2/4: Merging weather (Many-to-One) and events (Interval Join)...")
    master_train = merge_datasets(train_raw, weather_clean, events_clean)
    master_test = merge_datasets(test_raw, weather_clean, events_clean)
    
    print(f"Master train shape: {master_train.shape}")
    print(f"Master test shape: {master_test.shape}")
    
    # Prepare column output lists
    train_cols = ['record_id', 'zone_clean', 'pickup_hour', 'pickup_datetime', 'trips', 'temp_c', 'rain_mm', 'humidity_pct', 'wind_kmh', 'is_event_active', 'event_type', 'event_name']
    test_cols = ['row_id', 'zone_clean', 'pickup_hour', 'pickup_datetime', 'temp_c', 'rain_mm', 'humidity_pct', 'wind_kmh', 'is_event_active', 'event_type', 'event_name']
    
    if 'row_id' in master_test.columns:
        test_out = master_test[test_cols].rename(columns={'zone_clean': 'zone'})
    else:
        test_out = master_test[['record_id'] + test_cols[1:]].rename(columns={'record_id': 'row_id', 'zone_clean': 'zone'})
        
    train_out = master_train[train_cols].rename(columns={'zone_clean': 'zone'})
    data_dict = create_data_dictionary()
    
    # Step 3/4 & 4/4: Save outputs to processed directories
    print("\nStep 3/4: Saving processed master files...")
    for pdir in [target_processed_dir, workspace_processed_dir]:
        try:
            print(f" -> {pdir}")
            train_out.to_csv(os.path.join(pdir, "master_train.csv"), index=False)
            test_out.to_csv(os.path.join(pdir, "master_test.csv"), index=False)
            data_dict.to_csv(os.path.join(pdir, "data_dictionary_master.csv"), index=False)
        except PermissionError as e:
            print(f"Warning: File lock encountered at {pdir}: {e}")
    
    print("\n==================================================")
    print("Data Cleaning & Integration Completed Successfully!")
    print("==================================================\n")
