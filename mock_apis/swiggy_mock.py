import random
from datetime import datetime, timedelta

def generate_mock_earnings(worker_id: str, platform: str = "swiggy", weeks: int = 8):
    """
    Generate mock hourly earning history for a gig worker.
    Assumptions: 
    - Base off-peak: ₹40-60/hr
    - Peak times (Lunch 1pm-3pm, Dinner 7pm-10pm): ₹100-150/hr
    - Weekend multiplier: 1.2x
    """
    history = []
    end_date = datetime.now()
    start_date = end_date - timedelta(weeks=weeks)
    
    current_date = start_date
    while current_date <= end_date:
        # Assuming worker works 8 hours a day randomly
        for hour in range(8, 22):
            is_peak = (13 <= hour <= 15) or (19 <= hour <= 22)
            is_weekend = current_date.weekday() >= 5
            
            # Base earnings
            if is_peak:
                hourly_earning = random.randint(100, 150)
            else:
                hourly_earning = random.randint(40, 60)
                
            # Weekend multiplier
            if is_weekend:
                hourly_earning = int(hourly_earning * 1.2)
                
            # Randomly skip some hours (worker is offline)
            if random.random() > 0.3:
                history.append({
                    "timestamp": current_date.replace(hour=hour, minute=0, second=0).isoformat(),
                    "platform": platform,
                    "worker_id": worker_id,
                    "zone_id": "zone_koramangala_1",
                    "earnings_inr": hourly_earning,
                    "orders_completed": random.randint(1, 4) if hourly_earning > 60 else random.randint(0, 2)
                })
                
        current_date += timedelta(days=1)
        
    return history

if __name__ == "__main__":
    # Test generation
    data = generate_mock_earnings("worker_123")
    print(f"Generated {len(data)} hours of simulated data for worker_123.")
