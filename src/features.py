"""
src/features.py
----------------
Senior Data Engineer Feature Extraction Module
Built on the cleaned master_train.csv and master_test.csv schema.
"""

import os, sys
import numpy as np
import pandas as pd

def extract_features(df: pd.DataFrame, is_train: bool = True) -> pd.DataFrame:
    """
    Extract comprehensive features using zone_id and zone_clean.
    """
    df = df.copy()
    
    df['pickup_datetime'] = pd.to_datetime(df['pickup_datetime'])
    
    # 1. Calendar Features
    df['hour'] = df['pickup_datetime'].dt.hour
    df['dayofweek'] = df['pickup_datetime'].dt.dayofweek
    df['day'] = df['pickup_datetime'].dt.day
    df['month'] = df['pickup_datetime'].dt.month
    df['is_weekend'] = (df['dayofweek'] >= 5).astype(int)
    df['is_payday'] = df['day'].isin([1, 2, 3, 28, 29, 30, 31]).astype(int)
    
    # Cyclical hour features
    df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24.0)
    df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24.0)
    
    # 2. Weather Features & Rolling Rain
    df['rain_mm'] = df['rain_mm'].clip(lower=0).fillna(0.0)
    df['temp_c'] = df['temp_c'].ffill().bfill()
    df['humidity_pct'] = df['humidity_pct'].ffill().bfill()
    df['wind_kmh'] = df['wind_kmh'].ffill().bfill()
    
    # Rolling 3-hour precipitation sum per zone_id
    df = df.sort_values(['zone_id', 'pickup_datetime'])
    df['rain_3h_sum'] = df.groupby('zone_id')['rain_mm'].transform(lambda x: x.rolling(3, min_periods=1).sum())
    
    # Rain intensity classification
    df['rain_class'] = pd.cut(
        df['rain_mm'],
        bins=[-np.inf, 0.1, 2.5, 7.6, np.inf],
        labels=[0, 1, 2, 3]
    ).astype(int)
    
    # 3. Cross Interactions
    df['zone_x_rain'] = df['zone_id'].astype(str) + "_rain_" + df['rain_class'].astype(str)
    df['zone_x_hour'] = df['zone_id'].astype(str) + "_h_" + df['hour'].astype(str)
    
    # 4. Long-Term Demand Trend
    df['month_trend'] = df['month']
    
    return df.sort_index()

def add_historical_lags_and_aggregations(train_df: pd.DataFrame, test_df: pd.DataFrame) -> tuple:
    """
    Compute lags and historical zone-hourly aggregations based on zone_id.
    """
    train_df = train_df.copy()
    test_df = test_df.copy()
    
    combined = pd.concat([train_df, test_df], ignore_index=True).sort_values(['zone_id', 'pickup_datetime'])
    
    # Lags (24h, 48h, 168h, 336h)
    combined['lag_24h'] = combined.groupby('zone_id')['trips'].shift(24)
    combined['lag_48h'] = combined.groupby('zone_id')['trips'].shift(48)
    combined['lag_168h'] = combined.groupby('zone_id')['trips'].shift(168)
    combined['lag_336h'] = combined.groupby('zone_id')['trips'].shift(336)
    
    # Rolling 24h & 7d Mean and Std
    combined['rolling_24h_mean_trips'] = combined.groupby('zone_id')['trips'].transform(
        lambda x: x.shift(1).rolling(24, min_periods=6).mean()
    )
    combined['rolling_24h_std_trips'] = combined.groupby('zone_id')['trips'].transform(
        lambda x: x.shift(1).rolling(24, min_periods=6).std()
    )
    combined['rolling_7d_mean_trips'] = combined.groupby('zone_id')['trips'].transform(
        lambda x: x.shift(1).rolling(168, min_periods=24).mean()
    )
    
    # Historical Lookups
    zh_map = train_df.groupby(['zone_id', 'hour'])['trips'].mean().rename('zone_hour_mean_trips').reset_index()
    zdw_map = train_df.groupby(['zone_id', 'dayofweek', 'hour'])['trips'].mean().rename('zone_dow_hour_mean_trips').reset_index()
    
    train_len = len(train_df)
    train_res = combined.iloc[:train_len].copy()
    test_res = combined.iloc[train_len:].copy()
    
    train_res = pd.merge(train_res, zh_map, on=['zone_id', 'hour'], how='left')
    train_res = pd.merge(train_res, zdw_map, on=['zone_id', 'dayofweek', 'hour'], how='left')
    
    test_res = pd.merge(test_res, zh_map, on=['zone_id', 'hour'], how='left')
    test_res = pd.merge(test_res, zdw_map, on=['zone_id', 'dayofweek', 'hour'], how='left')
    
    # Impute missing values with baseline lookups
    overall_mean = train_df['trips'].mean()
    for col in ['lag_24h', 'lag_48h', 'lag_168h', 'lag_336h', 'rolling_24h_mean_trips', 'rolling_24h_std_trips', 'rolling_7d_mean_trips', 'zone_hour_mean_trips', 'zone_dow_hour_mean_trips']:
        train_res[col] = train_res[col].fillna(train_res['zone_dow_hour_mean_trips']).fillna(overall_mean)
        test_res[col] = test_res[col].fillna(test_res['zone_dow_hour_mean_trips']).fillna(overall_mean)
        
    return train_res.sort_index(), test_res.sort_index()
