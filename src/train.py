"""
src/train.py
-------------
High-Performance Model Training, Ensembling, Evaluation & Selection Pipeline
Qiyas Data Science & AI Hackathon - Addis Ride Demand Forecasting Challenge

Implements:
1. Target Variable Log Transformation (log1p / expm1) for heteroscedasticity stabilization.
2. Advanced Feature Matrix with 24h/48h/168h/336h Lags & Rolling Statistics.
3. Individual Regressors (CatBoost, LightGBM, HistGB, XGBoost, Random Forest, Ridge, Lasso).
4. Multi-Model Weighted Ensemble (CatBoost 40% + LightGBM 30% + HistGB 20% + XGBoost 10%).
"""

import os, sys, time, joblib
import numpy as np
import pandas as pd

from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import (
    RandomForestRegressor,
    GradientBoostingRegressor,
    HistGradientBoostingRegressor
)
from sklearn.metrics import (
    mean_squared_error,
    mean_absolute_error,
    r2_score,
    mean_absolute_percentage_error
)
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from src.features import extract_features, add_historical_lags_and_aggregations

# Import Gradient Boosting Frameworks
import xgboost as xgb
from xgboost import XGBRegressor

import lightgbm as lgb
from lightgbm import LGBMRegressor

from catboost import CatBoostRegressor

from sklearn.base import BaseEstimator, RegressorMixin

class WeightedEnsembleRegressor(BaseEstimator, RegressorMixin):
    """
    Weighted Ensemble of Top 4 Gradient Boosting Frameworks for Maximum R² Score.
    """
    def __init__(self, cat_weight=0.40, lgb_weight=0.30, hist_weight=0.20, xgb_weight=0.10):
        self.cat_weight = cat_weight
        self.lgb_weight = lgb_weight
        self.hist_weight = hist_weight
        self.xgb_weight = xgb_weight

    def fit(self, X, y):
        self.model_cat_ = CatBoostRegressor(iterations=300, depth=7, learning_rate=0.04, verbose=0, random_seed=42)
        self.model_lgb_ = LGBMRegressor(n_estimators=300, num_leaves=63, learning_rate=0.04, random_state=42, verbose=-1)
        self.model_hist_ = HistGradientBoostingRegressor(max_iter=300, max_depth=8, learning_rate=0.04, random_state=42)
        self.model_xgb_ = XGBRegressor(n_estimators=300, max_depth=7, learning_rate=0.04, random_state=42, n_jobs=-1)
        
        self.model_cat_.fit(X, y)
        self.model_lgb_.fit(X, y)
        self.model_hist_.fit(X, y)
        self.model_xgb_.fit(X, y)
        self.is_fitted_ = True
        return self

    def predict(self, X):
        pred_cat = self.model_cat_.predict(X)
        pred_lgb = self.model_lgb_.predict(X)
        pred_hist = self.model_hist_.predict(X)
        pred_xgb = self.model_xgb_.predict(X)
        
        return (
            self.cat_weight * pred_cat +
            self.lgb_weight * pred_lgb +
            self.hist_weight * pred_hist +
            self.xgb_weight * pred_xgb
        )

def calculate_rmse(y_true, y_pred):
    return np.sqrt(mean_squared_error(y_true, y_pred))

def get_candidate_models():
    return {
        "Weighted Ensemble (Top 4 Boosted Blend)": WeightedEnsembleRegressor(),
        "CatBoost": CatBoostRegressor(iterations=300, depth=7, learning_rate=0.04, verbose=0, random_seed=42),
        "LightGBM": LGBMRegressor(n_estimators=300, num_leaves=63, learning_rate=0.04, random_state=42, verbose=-1),
        "Hist Gradient Boosting": HistGradientBoostingRegressor(max_iter=300, max_depth=8, learning_rate=0.04, random_state=42),
        "XGBoost": XGBRegressor(n_estimators=300, max_depth=7, learning_rate=0.04, random_state=42, n_jobs=-1),
        "Ridge Regression": Ridge(alpha=1.0),
        "Lasso Regression": Lasso(alpha=0.1),
        "Linear Regression": LinearRegression()
    }

def prepare_feature_matrix(df: pd.DataFrame):
    feature_cols = [
        'hour', 'dayofweek', 'day', 'month', 'is_weekend', 'is_payday', 'hour_sin', 'hour_cos',
        'temp_c', 'rain_mm', 'humidity_pct', 'wind_kmh', 'rain_3h_sum', 'rain_class',
        'is_event_active', 'lag_24h', 'lag_48h', 'lag_168h', 'lag_336h',
        'rolling_24h_mean_trips', 'rolling_24h_std_trips', 'rolling_7d_mean_trips',
        'zone_hour_mean_trips', 'zone_dow_hour_mean_trips'
    ]
    categorical_cols = ['zone', 'event_type', 'zone_x_rain', 'zone_x_hour']
    
    X = df[feature_cols + categorical_cols]
    y = df['trips'] if 'trips' in df.columns else None
    
    return X, y, feature_cols, categorical_cols

def build_pipeline(model, feature_cols, categorical_cols):
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), feature_cols),
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_cols)
        ]
    )
    return Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('regressor', model)
    ])

def train_and_evaluate():
    print("\n==================================================")
    print("Executing High-Performance Model Training & Selection Pipeline")
    print("==================================================\n")
    
    pdir = os.path.join(base_dir, "data", "processed")
    models_dir = os.path.join(base_dir, "models")
    reports_dir = os.path.join(base_dir, "reports")
    os.makedirs(models_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)
    
    train_master = pd.read_csv(os.path.join(pdir, "master_train.csv"))
    test_master = pd.read_csv(os.path.join(pdir, "master_test.csv"))
    
    train_df = extract_features(train_master, is_train=True)
    test_df = extract_features(test_master, is_train=False)
    train_df, test_df = add_historical_lags_and_aggregations(train_df, test_df)
    
    # Chronological Split (Train < Oct 18, Val Oct 18 - Oct 31)
    train_df['pickup_datetime'] = pd.to_datetime(train_df['pickup_datetime'])
    split_date = pd.Timestamp('2025-10-18')
    
    train_sub = train_df[(train_df['pickup_datetime'] < split_date) & train_df['trips'].notna()].copy()
    val_sub = train_df[(train_df['pickup_datetime'] >= split_date) & train_df['trips'].notna()].copy()
    
    print(f"Chronological Train Split: {len(train_sub)} rows (Jan 1 - Oct 17)")
    print(f"Chronological Val Split:   {len(val_sub)} rows (Oct 18 - Oct 31)\n")
    
    X_train, y_train, feat_cols, cat_cols = prepare_feature_matrix(train_sub)
    X_val, y_val, _, _ = prepare_feature_matrix(val_sub)
    
    # Target Log Transformation (Strategy 1)
    y_train_log = np.log1p(y_train)
    
    candidate_models = get_candidate_models()
    results = []
    trained_pipelines = {}
    
    print("--- Training Models with Log Transformation & Advanced Features ---")
    for name, model in candidate_models.items():
        t0 = time.time()
        pipeline = build_pipeline(model, feat_cols, cat_cols)
        pipeline.fit(X_train, y_train_log)
        train_time = round(time.time() - t0, 2)
        
        # Predict & Inverse Transform (expm1)
        preds_log = pipeline.predict(X_val)
        preds = np.clip(np.expm1(preds_log), 0, None)
        
        rmse = calculate_rmse(y_val, preds)
        mae = mean_absolute_error(y_val, preds)
        r2 = r2_score(y_val, preds)
        mape = mean_absolute_percentage_error(y_val, preds)
        
        results.append({
            "Model Name": name,
            "Validation RMSE": round(rmse, 4),
            "Validation MAE": round(mae, 4),
            "R² Score": round(r2, 4),
            "MAPE": round(mape, 4),
            "Train Time (s)": train_time
        })
        trained_pipelines[name] = pipeline
        print(f" -> {name:40s} | RMSE: {rmse:7.4f} | MAE: {mae:7.4f} | R²: {r2:6.4f} | Time: {train_time}s")
        
    results_df = pd.DataFrame(results).sort_values("Validation RMSE")
    print("\n--- Final Model Leaderboard ---")
    print(results_df.to_string(index=False))
    
    results_df.to_csv(os.path.join(reports_dir, "model_comparison_leaderboard.csv"), index=False)
    
    best_model_name = results_df.iloc[0]["Model Name"]
    best_rmse = results_df.iloc[0]["Validation RMSE"]
    best_r2 = results_df.iloc[0]["R² Score"]
    
    print(f"\n TOP WINNING MODEL: '{best_model_name}' (Validation RMSE: {best_rmse} | R² Score: {best_r2})")
    
    winning_pipeline = trained_pipelines[best_model_name]
    model_artifact_path = os.path.join(models_dir, "final_model.joblib")
    joblib.dump(winning_pipeline, model_artifact_path)
    print(f"Saved winning model artifact to: {model_artifact_path}\n")

if __name__ == "__main__":
    train_and_evaluate()
