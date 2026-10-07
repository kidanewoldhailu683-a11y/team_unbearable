"""
src/correlations.py
--------------------
Feature Correlation Analysis for Addis Ride Demand Forecasting Challenge

Computes:
1. Pearson (linear) and Spearman (rank) correlations for every feature with target variable 'trips'.
2. Full Pairwise Feature Correlation Matrix.
3. Feature Correlation Heatmap saved to figures/fig_feature_correlations.png.
4. Summary leaderboard CSV saved to reports/feature_correlation_report.csv.
"""

import os, sys
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from src.features import extract_features, add_historical_demand_aggregations

def analyze_feature_correlations():
    print("\n==================================================")
    print("Executing Feature Correlation Analysis")
    print("==================================================\n")
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pdir = os.path.join(base_dir, "data", "processed")
    fig_dirs = [
        os.path.join(base_dir, "figures"),
        r"C:\Users\Administrator\Desktop\Projects\hackathon\figures"
    ]
    reports_dir = os.path.join(base_dir, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    
    # 1. Load Master Train Dataset
    train_master = pd.read_csv(os.path.join(pdir, "master_train.csv"))
    
    # Check if raw operational columns exist for correlation analysis (active_drivers, avg_wait_min, avg_fare_birr)
    raw_dir = os.path.join(base_dir, "dataset", "raw") if os.path.exists(os.path.join(base_dir, "dataset", "raw")) else os.path.join(base_dir, "data", "raw")
    raw_train = pd.read_csv(os.path.join(raw_dir, "ride_demand_train.csv"))
    
    # Merge operational columns if available
    if 'active_drivers' in raw_train.columns:
        train_master['active_drivers'] = raw_train['active_drivers']
        train_master['avg_wait_min'] = raw_train['avg_wait_min']
        train_master['avg_fare_birr'] = raw_train['avg_fare_birr']
        
    # Extract features
    df = extract_features(train_master, is_train=True)
    df, _ = add_historical_demand_aggregations(df, df)
    
    # Drop rows where target variable 'trips' is missing
    df = df.dropna(subset=['trips']).copy()
    
    # Select numeric features for correlation matrix
    numeric_cols = [
        'trips',
        'zone_dow_hour_mean_trips',
        'zone_hour_mean_trips',
        'hour',
        'hour_sin',
        'hour_cos',
        'is_weekend',
        'temp_c',
        'rain_mm',
        'humidity_pct',
        'wind_kmh',
        'rain_class',
        'is_event_active'
    ]
    
    if 'active_drivers' in df.columns:
        numeric_cols.extend(['active_drivers', 'avg_wait_min', 'avg_fare_birr'])
        
    corr_df = df[numeric_cols]
    
    # 2. Compute Pearson & Spearman Correlations with Target 'trips'
    pearson_corr = corr_df.corr(method='pearson')['trips'].rename('Pearson_r')
    spearman_corr = corr_df.corr(method='spearman')['trips'].rename('Spearman_rho')
    
    corr_summary = pd.DataFrame({'Pearson_r': pearson_corr, 'Spearman_rho': spearman_corr})
    corr_summary['Abs_Pearson'] = corr_summary['Pearson_r'].abs()
    corr_summary = corr_summary.sort_values('Abs_Pearson', ascending=False)
    
    print("--- Feature Correlation Leaderboard with Target 'trips' ---")
    print(corr_summary[['Pearson_r', 'Spearman_rho']].to_string())
    
    # Save Report
    csv_out = os.path.join(reports_dir, "feature_correlation_report.csv")
    corr_summary.to_csv(csv_out)
    print(f"\nSaved correlation report CSV to: {csv_out}")
    
    # 3. Plot Full Feature Correlation Heatmap
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(12, 10))
    
    full_corr = corr_df.corr(method='pearson')
    
    sns.heatmap(
        full_corr,
        annot=True,
        fmt='.2f',
        cmap='coolwarm',
        vmin=-1,
        vmax=1,
        linewidths=0.5,
        ax=ax,
        cbar_kws={'label': 'Pearson Correlation Coefficient (r)'}
    )
    ax.set_title("Full Pairwise Feature Correlation Matrix (Addis Ride Demand)", fontsize=14, fontweight='bold', pad=15)
    
    for fdir in fig_dirs:
        os.makedirs(fdir, exist_ok=True)
        fig_path = os.path.join(fdir, "fig_feature_correlations.png")
        fig.savefig(fig_path, dpi=150, bbox_inches='tight')
        print(f"Saved Correlation Heatmap: {fig_path}")
        
    plt.close(fig)
    print("\nFeature Correlation Analysis Completed Successfully!")

if __name__ == "__main__":
    analyze_feature_correlations()
