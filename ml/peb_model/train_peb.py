import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import joblib
import os

# Ensure models directory exists
os.makedirs('models', exist_ok=True)

def train_peb_model():
    print("🚀 Training PEB (Personal Earning Baseline) Linear Regression Model...")
    
    # 1. Generate Synthetic 8-Week Training Data (to mirror Swiggy/Zomato historicals)
    # Features: [day_of_week(0-6), time_slot(0-23), is_raining(0/1), zone_risk(0-100)]
    # Target: Earnings in INR
    np.random.seed(42)
    n_samples = 2000
    
    days = np.random.randint(0, 7, n_samples)
    slots = np.random.randint(0, 24, n_samples)
    risk = np.random.randint(20, 90, n_samples)
    is_raining = np.where(risk > 60, 1, 0)
    
    # Base formula: Base + Peak Hour Bonus + Rain Surge
    earnings = 150 + \
               (slots == 19) * 120 + \
               (slots == 13) * 80 + \
               (is_raining * 75) + \
               (days >= 5) * 50 + \
               np.random.normal(0, 20, n_samples)
               
    X = np.column_stack((days, slots, is_raining, risk))
    y = np.maximum(earnings, 0) # No negative earnings
    
    # 2. Train Model
    model = LinearRegression()
    model.fit(X, y)
    
    # 3. Save Model
    joblib.dump(model, 'models/peb_linear_regression.joblib')
    print(f"✅ PEB Model Trained. R² Score: {model.score(X, y):.3f}")
    print(f"   Saved to: ml/peb_model/models/peb_linear_regression.joblib\n")

if __name__ == "__main__":
    train_peb_model()
