import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np

class PEBEngine:
    def __init__(self):
        import os
        import joblib
        try:
            model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'models', 'peb_linear_regression.joblib')
            self.model = joblib.load(model_path)
        except Exception:
            self.model = None
        
    def train_baseline(self, earnings_data: list):
        """
        Calculates Personal Earning Baseline using trained Scikit-Learn Model.
        """
        if not earnings_data:
            return {"avg_hourly_inr": 0, "weekly_baseline_inr": 0, "total_slots_worked": 0}
            
        df = pd.DataFrame(earnings_data)
        df['datetime'] = pd.to_datetime(df['timestamp'])
        df['hour'] = df['datetime'].dt.hour
        df['day_of_week'] = df['datetime'].dt.dayofweek
        
        # We simulate passing the data to the model
        if self.model:
            # Model features: [day_of_week, time_slot, is_raining, risk]
            # Since this is historical, we mock historic rain=0 and risk=40
            X = np.column_stack((df['day_of_week'], df['hour'], np.zeros(len(df)), np.full(len(df), 40)))
            predictions = self.model.predict(X)
            average_hourly = predictions.mean()
        else:
            average_hourly = df['earnings_inr'].mean()
            
        WEEKLY_HOURS = 45  # Standard working week — consistent with plan recommender tiers
        average_weekly = average_hourly * WEEKLY_HOURS
        
        return {
            "avg_hourly_inr": round(average_hourly, 2),
            "weekly_baseline_inr": round(average_weekly, 2),
            "total_slots_worked": len(df),
            "linear_model_score": "Loaded via Joblib" if self.model else "Fallback"
        }

peb_engine = PEBEngine()
