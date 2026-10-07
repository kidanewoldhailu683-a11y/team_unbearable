"""
src/predict.py
---------------
Inference & Submission Generator for Addis Ride Demand Forecasting Challenge (Deliverable G4)

Key Responsibilities:
1. Load final trained model artifact from models/final_model.joblib.
2. Load master test dataset from data/processed/master_test.csv.
3. Extract features using src.features module.
4. Predict 4,032 hourly demand target values (Nov 1-14, 2025).
5. Format and save final submission CSV to submission/team_qiyas_ai_submission.csv.
"""

import os
import joblib
import pandas as pd
import numpy as np

import sys
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from src.features import extract_features, add_historical_lags_and_aggregations
from src.train import WeightedEnsembleRegressor

def generate_submission():
    """
    Generate submission prediction file.
    """
    print("\n==================================================")
    print("Executing Submission Generation Pipeline")
    print("==================================================\n")
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    model_path = os.path.join(base_dir, "models", "final_model.joblib")
    pdir = os.path.join(base_dir, "data", "processed")
    sub_dir = os.path.join(base_dir, "submission")
    os.makedirs(sub_dir, exist_ok=True)
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model artifact not found at {model_path}. Please run src/train.py first!")
        
    print(f"Loading trained model artifact from: {model_path}")
    pipeline = joblib.load(model_path)
    
    # Load Master Train & Test for Feature Aggregations
    train_master = pd.read_csv(os.path.join(pdir, "master_train.csv"))
    test_master = pd.read_csv(os.path.join(pdir, "master_test.csv"))
    
    train_df = extract_features(train_master, is_train=True)
    test_df = extract_features(test_master, is_train=False)
    train_df, test_df = add_historical_lags_and_aggregations(train_df, test_df)
    
    # Feature matrix setup
    feature_cols = [
        'hour', 'dayofweek', 'day', 'month', 'is_weekend', 'is_payday', 'hour_sin', 'hour_cos',
        'temp_c', 'rain_mm', 'humidity_pct', 'wind_kmh', 'rain_3h_sum', 'rain_class',
        'is_event_active', 'lag_24h', 'lag_48h', 'lag_168h', 'lag_336h',
        'rolling_24h_mean_trips', 'rolling_24h_std_trips', 'rolling_7d_mean_trips',
        'zone_hour_mean_trips', 'zone_dow_hour_mean_trips'
    ]
    categorical_cols = ['zone', 'event_type', 'zone_x_rain', 'zone_x_hour']
    
    X_test = test_df[feature_cols + categorical_cols]
    
    # Generate Predictions
    print(f"Predicting trip demand for {len(X_test)} test zone-hours...")
    preds_log = pipeline.predict(X_test)
    preds = np.clip(np.expm1(preds_log), 0, None)  # No negative trip forecasts
    
    # Format Submission
    sub_df = pd.DataFrame({
        "row_id": test_master["row_id"],
        "predicted_trips": np.round(preds, 2)
    })
    
    out_path = os.path.join(sub_dir, "team_qiyas_ai_submission.csv")
    sub_df.to_csv(out_path, index=False)
    
    print("\n--- Submission Integrity Checks (Deliverable G4) ---")
    assert len(sub_df) == 4032, f"FAIL: Expected 4032 rows, got {len(sub_df)}"
    assert sub_df['predicted_trips'].isnull().sum() == 0, "FAIL: Null values in predictions!"
    assert (sub_df['predicted_trips'] < 0).sum() == 0, "FAIL: Negative predictions found!"
    print("PASS: Exactly 4,032 valid non-negative trip predictions generated.")
    print(f"Final submission saved to: {out_path}\n")

if __name__ == "__main__":
    generate_submission()
