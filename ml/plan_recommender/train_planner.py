import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
import joblib
import os

os.makedirs('models', exist_ok=True)

def train_plan_recommender():
    print("🚀 Training Plan Recommender K-Means Clustering Model...")
  
    # Features: [weekly_hours, avg_safar_score, claims_history]
    np.random.seed(42)
    n_workers = 3000
    
    hours = np.random.gamma(shape=5.0, scale=8.0, size=n_workers) # Right skewed hours
    hours = np.clip(hours, 5, 100)
    scores = np.random.normal(45, 15, n_workers)
    claims = np.random.poisson(0.5, n_workers)
    
    X = np.column_stack((hours, scores, claims))
    
    # We want 5 clusters corresponding to [Light, Regular, Standard, Pro, Max]
    kmeans = KMeans(n_clusters=5, random_state=42, n_init='auto')
    kmeans.fit(X)
    
    joblib.dump(kmeans, 'models/kmeans_plan_recommender.joblib')
    print(f"✅ Recommender Trained. Grouped 3000 synthesized worker profiles into 5 Plan Tiers.")
    print(f"   Saved to: ml/plan_recommender/models/kmeans_plan_recommender.joblib\n")

if __name__ == "__main__":
    train_plan_recommender()
