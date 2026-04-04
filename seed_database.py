"""
SmartShift+ Database Seeder — 100 Realistic Workers
Generates workers with Indian names, runs ML models (PEB engine,
KMeans plan recommender, IsolationForest BPS) for each, and persists
everything to the SQLite database.

Run: python seed_database.py
"""
import sys, os, random
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.chdir(os.path.join(os.path.dirname(__file__), 'backend'))

from database import SessionLocal, Worker, WorkerPlan, init_db, engine
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

# ── Seed Data Pools ────────────────────────────────────────────────────────

FIRST_NAMES = [
    "Ravi", "Amit", "Suresh", "Priya", "Kavitha", "Deepak", "Anita", "Rajesh",
    "Sunita", "Vikram", "Meena", "Arjun", "Lakshmi", "Kiran", "Pooja", "Sandeep",
    "Rekha", "Manoj", "Bhavna", "Arun", "Shalini", "Rohit", "Usha", "Ganesh",
    "Divya", "Harish", "Padma", "Naresh", "Swathi", "Venkat", "Anand", "Saranya",
    "Prakash", "Geetha", "Sunil", "Nisha", "Ramesh", "Asha", "Sanjay", "Radha",
    "Ajay", "Savitha", "Kumar", "Hema", "Dinesh", "Vijaya", "Mohan", "Vani",
    "Srinivas", "Latha", "Balu", "Jyothi", "Mani", "Chitra", "Raja", "Sudha",
    "Anil", "Vimala", "Raju", "Jamuna", "Subbaiah", "Ratna", "Manikandan",
    "Sumathy", "Selvam", "Kamala", "Pandi", "Meenakshi", "Murugan", "Vasantha",
    "Kartik", "Deepa", "Naveen", "Archana", "Balaji", "Sowmya", "Vinayak",
    "Renuka", "Sathish", "Indira", "Chandru", "Nalini", "Durai", "Shanthi",
    "Pandian", "Ganga", "Ashwin", "Parvathi", "Karthik", "Yamini", "Sivakumar",
    "Malathi", "Shankar", "Thenmozhi", "Ezhil", "Mythili", "Raman", "Santhi",
    "Annamalai", "Kousalya", "Baskaran", "Thirumala"
]

LAST_NAMES = [
    "Kumar", "Sharma", "Reddy", "Singh", "Nair", "Pillai", "Rao", "Iyer",
    "Gowda", "Bhat", "Patel", "Verma", "Mishra", "Gupta", "Naidu", "Rajan",
    "Menon", "Krishnan", "Varma", "Murugan", "Subramaniam", "Raghavan",
    "Chettiar", "Naicker", "Pandian", "Selvakumar", "Balakrishnan", "Sundaram",
    "Parthasarathy", "Venkataraman", "Govindaraj", "Muthukumar", "Annamalai"
]

ZONES = [
    "Koramangala", "HSR Layout", "JP Nagar", "Indiranagar",
    "Whitefield", "Malleshwaram", "Marathahalli", "Yelahanka", "Electronic City"
]

ZONE_RISK_PROFILE = {
    "Koramangala":   "medium",
    "HSR Layout":    "low",
    "JP Nagar":      "medium",
    "Indiranagar":   "medium",
    "Whitefield":    "high",
    "Malleshwaram":  "low",
    "Marathahalli":  "high",
    "Yelahanka":     "low",
    "Electronic City": "medium"
}

PLATFORMS  = ["Swiggy", "Zomato", "Swiggy", "Zomato", "Swiggy"]  # Weighted towards Swiggy
CLAIM_HIST = ["zero_claims", "zero_claims", "zero_claims",
              "clean_approved", "clean_approved", "one_flagged", "multiple_flagged"]

# Hours per week profiles — maps to plan tier
HOURS_PROFILES = {
    "part_time":  range(8,  16),   # → Light plan
    "mid_time":   range(20, 36),   # → Regular plan
    "full_time":  range(40, 56),   # → Standard plan
    "heavy":      range(58, 72),   # → Pro plan
    "gig_max":    range(72, 90),   # → Max plan
}

HOUR_PROFILE_WEIGHTS = [0.15, 0.25, 0.35, 0.15, 0.10]

def pick_hours():
    profile = random.choices(
        list(HOURS_PROFILES.keys()), weights=HOUR_PROFILE_WEIGHTS
    )[0]
    return random.choice(list(HOURS_PROFILES[profile]))

def generate_phone():
    return "9" + "".join([str(random.randint(0, 9)) for _ in range(9)])

def generate_worker_id():
    return "W-" + str(random.randint(10000, 99999))

def mask_aadhaar():
    return str(random.randint(1000, 9999)) + "XXXXXXXX"

# ── ML Model Integration ────────────────────────────────────────────────────

def run_ml_pipeline(hours: int, zone_risk: str, claim_history: str):
    """Run PEB engine + KMeans plan recommender for a worker."""
    from services.plan_recommender import PlanRecommender
    from mock_apis.swiggy_mock import generate_mock_earnings
    from services.peb_engine import peb_engine

    # 1. Generate 8-week earnings history
    try:
        earnings_data = generate_mock_earnings("W-SEED")
        baseline = peb_engine.train_baseline(earnings_data)
        peb_weekly = round(baseline.get("weekly_baseline_inr", 0), 2)
    except Exception:
        # Fallback: compute from hours
        avg_hourly = random.uniform(55, 120)
        peb_weekly = round(hours * avg_hourly, 2)

    # 2. KMeans plan recommendation
    plan_data = PlanRecommender.generate_plan_offerings(hours, zone_risk, claim_history)
    recommended_id = plan_data["recommended_plan_id"]
    z_mult = plan_data["multipliers_applied"]["zone_risk"]
    c_mult = plan_data["multipliers_applied"]["claim_history"]

    chosen = next((p for p in plan_data["plans"] if p["id"] == recommended_id),
                  plan_data["plans"][2])  # Default to Standard

    return {
        "peb_weekly":     peb_weekly,
        "recommended_id": recommended_id,
        "plan":           chosen,
        "z_mult":         z_mult,
        "c_mult":         c_mult,
    }

def run_bps_check():
    """Run IsolationForest BPS for a typical genuine worker."""
    from services.trustmesh import TrustMeshEngine
    sensors = {
        "mock_location_flag": False,
        "gps_variance_std": round(random.uniform(3.0, 8.0), 2),
        "accelerometer_active": True,
        "speed_kmh": random.randint(15, 50),
        "orders_last_4_hrs": random.randint(2, 8),
        "zone_history_verified": True
    }
    bps, verdict = TrustMeshEngine.evaluate_bps(sensors)
    return bps, verdict


# ── Seeder ──────────────────────────────────────────────────────────────────

def seed_100_workers():
    init_db()

    db: Session = SessionLocal()
    try:
        existing = db.query(Worker).count()
        print(f"[SEED] Existing workers in DB: {existing}")

        used_phones    = {w.phone for w in db.query(Worker).all()}
        used_worker_ids = {w.worker_id for w in db.query(Worker).all()}

        workers_added  = 0
        target         = 100

        print(f"[SEED] Adding {target} workers with ML-computed plans...\n")
        print(f"{'#':>3}  {'Worker ID':<10}  {'Name':<22}  {'Platform':<8}  "
              f"{'Zone':<16}  {'Hours':>5}  {'PEB':>7}  {'Plan':<10}  "
              f"{'Premium':>8}  {'BPS':>4}  {'Claim History'}")
        print("-" * 120)

        while workers_added < target:
            # Generate identity
            name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
            zone = random.choice(ZONES)
            zone_risk = ZONE_RISK_PROFILE[zone]
            platform = random.choice(PLATFORMS)
            claim_history = random.choices(CLAIM_HIST,
                weights=[30, 30, 5, 20, 20, 10, 5][:len(CLAIM_HIST)])[0]
            hrs = pick_hours()

            # Unique IDs
            phone = generate_phone()
            while phone in used_phones:
                phone = generate_phone()
            used_phones.add(phone)

            wid = generate_worker_id()
            while wid in used_worker_ids:
                wid = generate_worker_id()
            used_worker_ids.add(wid)

            # Run ML pipeline
            ml = run_ml_pipeline(hrs, zone_risk, claim_history)
            bps, verdict = run_bps_check()

            # Random created_at (last 90 days)
            days_ago = random.randint(0, 89)
            created = datetime.utcnow() - timedelta(days=days_ago)

            # Persist Worker
            worker = Worker(
                worker_id    = wid,
                phone        = phone,
                name         = name,
                aadhaar      = mask_aadhaar(),
                zone         = zone,
                platform     = platform,
                zone_risk    = zone_risk,
                claim_history= claim_history,
                active_plan  = ml["plan"]["tier"],
                kyc_verified = True,
                created_at   = created,
            )
            db.add(worker)
            db.flush()  # Get worker.id

            # Persist WorkerPlan
            plan = WorkerPlan(
                worker_db_id    = worker.id,
                plan_id         = ml["plan"]["id"],
                plan_tier       = ml["plan"]["tier"],
                final_premium   = ml["plan"]["final_premium_inr"],
                coverage_ratio  = ml["plan"]["coverage_ratio_percent"] / 100,
                max_payout      = ml["plan"]["max_coverage_inr"],
                zone_multiplier = ml["z_mult"],
                claim_multiplier= ml["c_mult"],
                active          = True,
                activated_at    = created,
            )
            db.add(plan)

            workers_added += 1
            print(f"{workers_added:>3}  {wid:<10}  {name:<22}  {platform:<8}  "
                  f"{zone:<16}  {hrs:>5}h  "
                  f"Rs{ml['peb_weekly']:>6.0f}  {ml['plan']['tier']:<10}  "
                  f"Rs{ml['plan']['final_premium_inr']:>5}  {bps:>3}  {claim_history}")

        db.commit()
        print(f"\n[SEED] Done! {workers_added} workers added to database.")
        print(f"[SEED] Total workers now: {db.query(Worker).count()}")
        print(f"[SEED] Total plans now:   {db.query(WorkerPlan).count()}")

        # Show plan distribution
        from collections import Counter
        plans = [w.active_plan for w in db.query(Worker).all()]
        dist  = Counter(plans)
        print(f"\n[SEED] Plan distribution:")
        for tier, count in sorted(dist.items()):
            bar = "█" * (count // 2)
            print(f"  {tier:<12} {count:>3} workers  {bar}")

        # Show zone distribution
        zones_dist = Counter(w.zone for w in db.query(Worker).all())
        print(f"\n[SEED] Zone distribution:")
        for zone, count in sorted(zones_dist.items(), key=lambda x: -x[1]):
            bar = "█" * (count // 3)
            print(f"  {zone:<18} {count:>3} workers  {bar}")

    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        print(f"[SEED] ERROR: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')
    seed_100_workers()
