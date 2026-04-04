from auth_utils import generate_worker_id
from database import init_db, SessionLocal, Worker, Plan, ZoneScore, PEBBaseline, BillingRecord
from datetime import datetime, timedelta
import random

def seed():
    print("Initializing Database with Command Center Schema...")
    init_db()
    db = SessionLocal()
    try:
        # 1. Seed Workers
        platforms = ["Swiggy", "Zomato", "UberEats", "Zepto"]
        zones = ["Koramangala", "HSR Layout", "Indiranagar", "Whitefield", "Jayanagar", "JP Nagar", "Malleshwaram", "Marathahalli"]
        first_names = ["Rajesh", "Suresh", "Amit", "Priya", "Ankit", "Deepak", "Sunita", "Rahul"]
        last_names = ["Kumar", "Sharma", "Nair", "Patil", "Reddy", "Singh", "Biswas", "Gupta"]
        
        workers = []
        for i in range(1, 106):
            w = Worker(
                worker_id=generate_worker_id(),
                name=f"{random.choice(first_names)} {random.choice(last_names)}",
                phone=f"+9190000{i:05}",
                aadhaar=f"hash_{i}xyz",
                platform=random.choice(platforms),
                zone=random.choice(zones),
                kyc_verified=True,
                upi_id=f"worker{i}@okicici",
                razorpay_mandate_id=f"man_{random.randint(10000, 99999)}",
                trust_score=random.uniform(70, 100)
            )
            db.add(w)
            workers.append(w)
        
        db.commit() # Commit to get IDs
        print(f"Seeded {len(workers)} Workers.")

        # 2. Seed Plans (Active and History)
        tiers = {
            "Light": {"prem": 99, "hrs": 25},
            "Regular": {"prem": 249, "hrs": 45},
            "Standard": {"prem": 499, "hrs": 55},
            "Pro": {"prem": 899, "hrs": 70},
            "Max": {"prem": 1299, "hrs": 90}
        }
        
        for w in workers:
            tier_name = random.choice(list(tiers.keys()))
            t_data = tiers[tier_name]
            
            p = Plan(
                worker_id=w.id,
                tier=tier_name,
                covered_hrs_per_week=t_data["hrs"],
                base_premium=t_data["prem"],
                final_weekly_premium=t_data["prem"] * random.uniform(0.9, 1.2),
                active=True,
                valid_from=datetime.utcnow() - timedelta(days=10)
            )
            db.add(p)
        
        db.commit()
        print("Seeded Active Plans.")

        # 3. Seed Zone Scores (Snapshots)
        for zone in zones:
            for h in range(24):
                z = ZoneScore(
                    zone_id=zone,
                    score=random.randint(15, 80),
                    rain_mm=random.uniform(0, 10),
                    recorded_at=datetime.utcnow() - timedelta(hours=h)
                )
                db.add(z)
        
        db.commit()
        print("Seeded Zone History.")

        # 4. Seed PEB Baselines
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        slots = ["06-10", "10-14", "14-18", "18-22", "22-02"]
        
        # Only seed for first 10 workers for speed
        for w in workers[:10]:
            for d in days:
                for s in slots:
                    peb = PEBBaseline(
                        worker_id=w.id,
                        day_of_week=d,
                        time_slot=s,
                        zone_id=w.zone,
                        expected_earnings=random.uniform(150, 600)
                    )
                    db.add(peb)
        
        db.commit()
        print("Seeded PEB AI Baselines.")

        # 5. Seed some billing failures for the dashboard
        for w in workers[20:23]:
            b = BillingRecord(
                worker_id=w.id,
                status="failed",
                amount=249,
                billed_at=datetime.utcnow() - timedelta(days=2)
            )
            db.add(b)
        
        db.commit()
        print("Seeded Billing Alerts.")

        print("--- RE-SEED COMPLETE (COMMAND CENTER SCHEMA) ---")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
