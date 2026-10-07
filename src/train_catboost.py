"""
src/train_catboost.py
----------------------
Single Best Model Training, Evaluation Metrics & Feature Importance Pipeline
Qiyas Data Science & AI Hackathon - Addis Ride Demand Forecasting Challenge

Selected Best Single Model: CatBoostRegressor
Trained on clean master_train.csv and master_test.csv.
"""

import os, sys, time, joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, mean_absolute_percentage_error
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from catboost import CatBoostRegressor

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from src.features import extract_features, add_historical_lags_and_aggregations

def train_best_single_model():
    print("\n==================================================")
    print("Training Best Single Model: CatBoostRegressor")
    print("==================================================\n")
    
    pdir = os.path.join(base_dir, "data", "processed")
    models_dir = os.path.join(base_dir, "models")
    fig_dirs = [
        os.path.join(base_dir, "figures"),
        r"C:\Users\Administrator\Desktop\Projects\hackathon\figures"
    ]
    reports_dir = os.path.join(base_dir, "reports")
    sub_dir = os.path.join(base_dir, "submission")
    
    os.makedirs(models_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)
    os.makedirs(sub_dir, exist_ok=True)
    
    # 1. Load Master Datasets
    train_master = pd.read_csv(os.path.join(pdir, "master_train.csv"))
    test_master = pd.read_csv(os.path.join(pdir, "master_test.csv"))
    
    # Extract Features
    train_df = extract_features(train_master, is_train=True)
    test_df = extract_features(test_master, is_train=False)
    train_df, test_df = add_historical_lags_and_aggregations(train_df, test_df)
    
    # Chronological Validation Split (Train < Oct 18, Val Oct 18 - Oct 31)
    train_df['pickup_datetime'] = pd.to_datetime(train_df['pickup_datetime'])
    split_date = pd.Timestamp('2025-10-18')
    
    train_sub = train_df[(train_df['pickup_datetime'] < split_date) & train_df['trips'].notna()].copy()
    val_sub = train_df[(train_df['pickup_datetime'] >= split_date) & train_df['trips'].notna()].copy()
    
    print(f"Chronological Train Split: {len(train_sub)} rows (Jan 1 - Oct 17)")
    print(f"Chronological Val Split:   {len(val_sub)} rows (Oct 18 - Oct 31)\n")
    
    # Define Numerical and Categorical Features from New Schema
    feature_cols = [
        'hour', 'dayofweek', 'day', 'month', 'is_weekend', 'is_payday', 'hour_sin', 'hour_cos',
        'temp_c', 'rain_mm', 'humidity_pct', 'wind_kmh', 'rain_3h_sum', 'rain_class',
        'has_event', 'event_count', 'has_sports', 'has_concert', 'has_public_holiday', 'event_attendance',
        'lag_24h', 'lag_48h', 'lag_168h', 'lag_336h',
        'rolling_24h_mean_trips', 'rolling_24h_std_trips', 'rolling_7d_mean_trips',
        'zone_hour_mean_trips', 'zone_dow_hour_mean_trips'
    ]
    # Filter features that exist in dataframe
    feature_cols = [c for c in feature_cols if c in train_sub.columns]
    categorical_cols = ['zone_clean', 'zone_x_rain', 'zone_x_hour']
    categorical_cols = [c for c in categorical_cols if c in train_sub.columns]
    
    X_train = train_sub[feature_cols + categorical_cols]
    y_train = train_sub['trips']
    
    X_val = val_sub[feature_cols + categorical_cols]
    y_val = val_sub['trips']
    
    X_test = test_df[feature_cols + categorical_cols]
    
    # 2. Build Preprocessor & CatBoost Model Pipeline
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), feature_cols),
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_cols)
        ]
    )
    
    catboost_model = CatBoostRegressor(
        iterations=350,
        depth=7,
        learning_rate=0.04,
        l2_leaf_reg=3,
        random_seed=42,
        verbose=0
    )
    
    pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('regressor', catboost_model)
    ])
    
    print("Fitting CatBoostRegressor model on new master training dataset...")
    t0 = time.time()
    pipeline.fit(X_train, y_train)
    fit_time = round(time.time() - t0, 2)
    
    # 3. Predict & Compute Evaluation Metrics
    preds = pipeline.predict(X_val)
    preds = np.clip(preds, 0, None)
    
    rmse = np.sqrt(mean_squared_error(y_val, preds))
    mae = mean_absolute_error(y_val, preds)
    r2 = r2_score(y_val, preds)
    mape = mean_absolute_percentage_error(y_val, preds)
    
    print("\n==================================================")
    print("REVISED CATBOOST EVALUATION METRICS SUMMARY")
    print("==================================================")
    print(f" -> Root Mean Squared Error (RMSE) : {rmse:.4f}")
    print(f" -> Mean Absolute Error (MAE)      : {mae:.4f}")
    print(f" -> R² Score (Variance Explained) : {r2:.4f} ({r2*100:.2f}%)")
    print(f" -> Training Time                  : {fit_time} seconds")
    print("==================================================\n")
    
    # Save Metrics CSV
    metrics_df = pd.DataFrame([{
        "Model": "CatBoostRegressor",
        "RMSE": round(rmse, 4),
        "MAE": round(mae, 4),
        "R2_Score": round(r2, 4),
        "MAPE": round(mape, 4),
        "Training_Time_Sec": fit_time
    }])
    metrics_df.to_csv(os.path.join(reports_dir, "catboost_evaluation_summary.csv"), index=False)
    
    # Save Final Winning Model Artifact
    model_artifact_path = os.path.join(models_dir, "final_model.joblib")
    joblib.dump(pipeline, model_artifact_path)
    print(f"Saved trained CatBoost artifact to: {model_artifact_path}")
    
    # 4. Generate Predictions for Test Submission
    test_preds = np.clip(pipeline.predict(X_test), 0, None)
    
    row_key = 'row_id' if 'row_id' in test_master.columns else 'record_id'
    sub_df = pd.DataFrame({
        "row_id": test_master[row_key],
        "predicted_trips": np.round(test_preds, 2)
    })
    sub_path = os.path.join(sub_dir, "team_qiyas_ai_submission.csv")
    try:
        sub_df.to_csv(sub_path, index=False)
        print(f"Updated predictions saved to: {sub_path}")
    except PermissionError:
        alt_sub_path = os.path.join(sub_dir, "team_qiyas_ai_submission_v2.csv")
        sub_df.to_csv(alt_sub_path, index=False)
        print(f"Warning: Primary submission file locked by another process. Saved to: {alt_sub_path}")
    
    # 5. DIAGRAM 1: Evaluation Metrics & Residuals Plot
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    ax1.scatter(y_val, preds, alpha=0.4, color='#2b5c8f', edgecolors='none', s=15)
    ax1.plot([0, y_val.max()], [0, y_val.max()], '--', color='#e74c3c', linewidth=2, label='Perfect 1:1 Line')
    ax1.set_title(f"CatBoost Actual vs Predicted Trips (R² = {r2:.4f})", fontsize=13, fontweight='bold')
    ax1.set_xlabel("Actual Hourly Trips", fontsize=11)
    ax1.set_ylabel("Predicted Hourly Trips", fontsize=11)
    ax1.legend(loc='upper left')
    
    residuals = y_val - preds
    sns.histplot(residuals, kde=True, ax=ax2, color='#2ecc71', bins=40)
    ax2.axvline(0, color='#e74c3c', linestyle='--', linewidth=2)
    ax2.set_title(f"Residual Error Distribution (MAE = {mae:.2f} trips)", fontsize=13, fontweight='bold')
    ax2.set_xlabel("Residual Error (Actual - Predicted)")
    ax2.set_ylabel("Frequency Count")
    
    plt.suptitle("CatBoost Evaluation Metrics & Residual Analysis", fontsize=15, fontweight='bold', y=1.03)
    
    for fdir in fig_dirs:
        os.makedirs(fdir, exist_ok=True)
        fig.savefig(os.path.join(fdir, "fig_catboost_metrics.png"), dpi=150, bbox_inches='tight')
    plt.close(fig)
    print("Saved Evaluation Metrics Diagram: figures/fig_catboost_metrics.png")
    
    # 6. DIAGRAM 2: Feature Importance Plot
    raw_catboost = pipeline.named_steps['regressor']
    encoded_feature_names = pipeline.named_steps['preprocessor'].get_feature_names_out()
    importances = raw_catboost.get_feature_importance()
    
    feature_imp_map = {}
    for name, imp in zip(encoded_feature_names, importances):
        root_name = name.split('__')[-1].split('_rain_')[0].split('_h_')[0]
        if 'zone' in root_name:
            root_name = 'zone'
        feature_imp_map[root_name] = feature_imp_map.get(root_name, 0.0) + imp
        
    imp_df = pd.DataFrame(list(feature_imp_map.items()), columns=['Feature', 'Importance']).sort_values('Importance', ascending=False)
    
    fig, ax = plt.subplots(figsize=(11, 7))
    colors = ['#2ecc71' if ('lag' in f or 'mean' in f) else ('#3498db' if 'rain' in f or 'temp' in f else '#34495e') for f in imp_df['Feature']]
    
    bars = ax.barh(imp_df['Feature'][::-1], imp_df['Importance'][::-1], color=colors[::-1], height=0.6)
    ax.set_title("CatBoost Feature Importance Breakdown (Revised Master Schema)", fontsize=14, fontweight='bold', pad=12)
    ax.set_xlabel("Relative Feature Importance Weight (%)", fontsize=12)
    
    for fdir in fig_dirs:
        os.makedirs(fdir, exist_ok=True)
        fig.savefig(os.path.join(fdir, "fig12_feature_importance.png"), dpi=150, bbox_inches='tight')
    plt.close(fig)
    print("Saved Feature Importance Diagram: figures/fig12_feature_importance.png")

if __name__ == "__main__":
    train_best_single_model()
