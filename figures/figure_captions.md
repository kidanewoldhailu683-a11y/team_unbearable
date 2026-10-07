# Deliverable C: Visualization Pack Captions & Data Audit

All figures generated at 150 DPI adhering to senior data visualization standards.

1. **Figure 1 (fig01_gaps_and_missingness.png)**: Audit of missing value percentages across raw tables prior to cleaning.
2. **Figure 2 (fig02_before_after_cleaning.png)**: Temperature distributions comparing raw uncleaned weather data against the cleaned and median-imputed master dataset.
3. **Figure 3 (fig03_demand_trend_with_holidays.png)**: Time-series of daily citywide ride demand from January through October 2025, with vertical lines marking key public holidays.
4. **Figure 4 (fig04_hour_by_weekday_heatmap.png)**: 24-hour demand heatmaps across days of the week, displaying morning (8:00 AM) and evening (5:00 PM - 6:00 PM) rush hour peaks.
5. **Figure 5 (fig05_zone_profiles.png)**: Hourly demand curves broken down by top commercial and residential zones (Bole, Kazanchis, Piazza, Merkato).
6. **Figure 6 (fig06_weather_timezone_check.png)**: Clock alignment verification proving the raw UTC weather timestamp shift to EAT (UTC+3 Addis Ababa local time).
7. **Figure 7 (fig07_rain_effect.png)**: Impact of rainfall intensity classes on average hourly trip volume.
8. **Figure 8 (fig08_event_study.png)**: Demand comparison between standard operating hours and hours with active citywide or local events.
9. **Figure 9 (fig09_holiday_effects.png)**: Ride demand index on recognized national public holidays versus normal operational days.
10. **Figure 10 (fig10_model_comparison.png)**: Leaderboard comparing validation R² scores across all 10 candidate regression models, highlighting the winning CatBoostRegressor (R² = 0.6280).
11. **Figure 11 (fig11_forecast_vs_actual.png)**: Line plot comparing ground truth trip volume against CatBoost predicted forecasts over the validation period.
12. **Figure 12 (fig12_feature_importance.png)**: Feature importance weights from the trained CatBoost pipeline, highlighting key temporal, weather, and event predictors.
