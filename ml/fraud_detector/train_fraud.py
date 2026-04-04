import numpy as np
from sklearn.ensemble import IsolationForest
import joblib
import os

os.makedirs('models', exist_ok=True)

def train_trustmesh_fraud_detector():
    print("🚀 Training TrustMesh (BPS) Isolation Forest Model...")
    
    # 1. Generate Synthetic TrustMesh Sensor Data
    # Features: [mock_location_prob, gps_variance, accel_variance, velocity_continuity, zone_history]
    np.random.seed(42)
    
    # Genuine workers (majority)
    n_genuine = 5000
    mock_loc_g = np.random.uniform(0, 0.05, n_genuine)  # No mock location
    gps_var_g = np.random.normal(5.0, 1.0, n_genuine)   # Natural drift
    accel_g = np.random.normal(2.5, 0.5, n_genuine)     # Natural bike vibration
    vel_cont_g = np.random.uniform(0.8, 1.0, n_genuine) # Smooth velocity
    zone_hist_g = np.random.randint(10, 500, n_genuine) # High history
    
    gen_data = np.column_stack((mock_loc_g, gps_var_g, accel_g, vel_cont_g, zone_hist_g))
    
    # Fake / Spoofers (Syndicate)
    n_fake = 200
    mock_loc_f = np.random.uniform(0.9, 1.0, n_fake)    # High spoof probability
    gps_var_f = np.random.normal(0.001, 0.001, n_fake)  # Zero drift (pinned)
    accel_f = np.random.normal(0.1, 0.05, n_fake)       # Sitting on sofa
    vel_cont_f = np.random.uniform(0.1, 0.4, n_fake)    # Teleportation
    zone_hist_f = np.random.randint(0, 2, n_fake)       # Never worked here
    
    fake_data = np.column_stack((mock_loc_f, gps_var_f, accel_f, vel_cont_f, zone_hist_f))
    
    # Train only on genuine data (Unsupervised anomaly detection)
    model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
    model.fit(gen_data)
    
    # Evaluate
    X_test = np.vstack((gen_data[:100], fake_data))
    y_pred = model.predict(X_test) # 1 for inlier, -1 for outlier
    outliers_caught = np.sum(y_pred[100:] == -1)
    
    print(f"✅ Fraud Detector Trained. Caught {outliers_caught}/{n_fake} simulated syndicate spoofers.")
    joblib.dump(model, 'models/isolation_forest_bps.joblib')
    print(f"   Saved to: ml/fraud_detector/models/isolation_forest_bps.joblib\n")

if __name__ == "__main__":
    train_trustmesh_fraud_detector()
