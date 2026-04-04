import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
import joblib
import os

os.makedirs('models', exist_ok=True)

def train_score_predictor():
    print("🚀 Training SafarScore 48-Hour Predictor (Gradient Boosting)...")
    
    # Features: [current_score, forecast_rain_mm, forecast_wind_kmh, forecast_temp_c]
    # Target: t+48 hours SafarScore (0-100)
    np.random.seed(42)
    n_samples = 1500
    
    current = np.random.randint(20, 70, n_samples)
    r_mm = np.random.exponential(5, n_samples)
    w_kmh = np.abs(np.random.normal(10, 5, n_samples))  # wind speed is non-negative
    temp = np.random.normal(30, 5, n_samples)
    
    # Mathematical relation for Target
    target_score = current * 0.3 + (r_mm * 3.5) + (w_kmh * 0.5) + np.maximum(temp-35, 0)*2
    target_score = np.clip(target_score + np.random.normal(0, 5, n_samples), 0, 100)
    
    X = np.column_stack((current, r_mm, w_kmh, temp))
    
    model = GradientBoostingRegressor(n_estimators=50, random_state=42)
    model.fit(X, target_score)
    
    joblib.dump(model, 'models/gbr_safarscore_predictor.joblib')
    print(f"✅ Predictor Trained. R² Score: {model.score(X, target_score):.3f}")
    print(f"   Saved to: ml/score_predictor/models/gbr_safarscore_predictor.joblib\n")

if __name__ == "__main__":
    train_score_predictor()
