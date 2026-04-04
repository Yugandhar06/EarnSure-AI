import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./smartshift.db")

def create_resilient_engine(url):
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args)

engine = create_resilient_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ─── High-Fidelity Domain Models ──────────────────────────────────────────────

class Worker(Base):
    """The master identity record. Stores identity, mandate, and reputation."""
    __tablename__ = "workers"
    id                  = Column(Integer, primary_key=True, index=True)
    worker_id           = Column(String, unique=True, index=True)
    name                = Column(String, nullable=True)
    phone               = Column(String, unique=True, index=True)
    aadhaar             = Column(String, nullable=True)
    platform            = Column(String, nullable=True) # Swiggy, Zomato, etc.
    zone                = Column(String, nullable=True) # e.g. 'Koramangala'
    kyc_verified        = Column(Boolean, default=False)
    zone_risk           = Column(String, default="medium")
    claim_history       = Column(String, default="zero_claims")
    upi_id              = Column(String, nullable=True)
    razorpay_mandate_id = Column(String, nullable=True)
    active_plan         = Column(String, nullable=True) # e.g. 'Pro'
    created_at          = Column(DateTime, default=datetime.utcnow)
    trust_score         = Column(Float, default=100.0) # 0-100 rolling repute

    plans       = relationship("Plan", back_populates="worker")
    shifts      = relationship("ShiftSession", back_populates="worker")
    payouts     = relationship("PayoutEvent", back_populates="worker")
    baselines   = relationship("PEBBaseline", back_populates="worker")
    billing     = relationship("BillingRecord", back_populates="worker")


class Plan(Base):
    """Worker plan history. Append-only history model (valid_from/to)."""
    __tablename__ = "plans"
    id                    = Column(Integer, primary_key=True, index=True)
    worker_id             = Column(Integer, ForeignKey("workers.id"))
    tier                  = Column(String) # light, regular, standard, pro, max
    plan_tier             = Column(String, nullable=True) # Alias used in logic
    covered_hrs_per_week  = Column(Integer, default=45)
    base_premium          = Column(Float)
    final_premium         = Column(Float, nullable=True) # Used in auth.py
    final_weekly_premium  = Column(Float)
    coverage_ratio        = Column(Float, default=0.70)
    max_payout            = Column(Float, nullable=True)
    zone_multiplier       = Column(Float, default=1.0)
    claim_history_factor  = Column(Float, default=1.0)
    claim_multiplier      = Column(Float, default=1.0)
    active                = Column(Boolean, default=True)
    activated_at          = Column(DateTime, default=datetime.utcnow)
    valid_from            = Column(DateTime, default=datetime.utcnow)
    valid_to              = Column(DateTime, nullable=True)

    worker = relationship("Worker", back_populates="plans")


class ZoneScore(Base):
    """Append-only time-series for 15-minute sensor snapshots."""
    __tablename__ = "zone_scores"
    id             = Column(Integer, primary_key=True, index=True)
    zone_id        = Column(String, index=True)
    score          = Column(Float) # 0-100 composite
    rain_mm        = Column(Float, default=0.0)
    aqi            = Column(Float, default=50.0)
    temp_c         = Column(Float, default=28.0)
    order_drop_pct = Column(Float, default=0.0)
    wind_kph       = Column(Float, default=0.0)
    strike_alert   = Column(Boolean, default=False)
    flood_alert    = Column(Boolean, default=False)
    recorded_at    = Column(DateTime, default=datetime.utcnow)


class ShiftSession(Base):
    """Tracks active shifts and protects against double payouts."""
    __tablename__ = "shift_sessions"
    id               = Column(Integer, primary_key=True, index=True)
    worker_id        = Column(Integer, ForeignKey("workers.id"))
    plan_id          = Column(Integer, ForeignKey("plans.id"))
    zone_id          = Column(String)
    started_at       = Column(DateTime, default=datetime.utcnow)
    ended_at         = Column(DateTime, nullable=True)
    hours_used       = Column(Float, default=0.0)
    payout_triggered = Column(Boolean, default=False) # Prevents double-trigger

    worker = relationship("Worker", back_populates="shifts")
    bps_logs = relationship("BPSLog", back_populates="shift")


class PayoutEvent(Base):
    """The financial ledger including parametric breakdown."""
    __tablename__ = "payout_events"
    id                = Column(Integer, primary_key=True, index=True)
    worker_id         = Column(Integer, ForeignKey("workers.id"))
    shift_session_id  = Column(Integer, ForeignKey("shift_sessions.id"))
    peb_amount        = Column(Float) # From peb_baselines
    actual_earnings   = Column(Float)
    gap_amount        = Column(Float)
    coverage_ratio    = Column(Float)
    signal_confidence = Column(Float)
    payout_amount     = Column(Float)
    razorpay_txn_id   = Column(String, nullable=True)
    status            = Column(String, default="pending") # pending, paid, failed
    triggered_at      = Column(DateTime, default=datetime.utcnow)
    paid_at           = Column(DateTime, nullable=True)

    worker = relationship("Worker", back_populates="payouts")


class BPSLog(Base):
    """Primary fraud audit trail (Behavioral Probability Score)."""
    __tablename__ = "bps_logs"
    id                 = Column(Integer, primary_key=True, index=True)
    shift_session_id   = Column(Integer, ForeignKey("shift_sessions.id"))
    bps_score          = Column(Integer) # 0-100
    mock_location_flag = Column(Boolean, default=False)
    gps_variance       = Column(Float, default=0.0)
    accelerometer_ok   = Column(Boolean, default=True)
    velocity_ok        = Column(Boolean, default=True)
    prior_zone_orders  = Column(Integer, default=0)
    ring_cluster_flag  = Column(Boolean, default=False)
    decision           = Column(String) # auto_approved, soft_flag, hard_flag, blocked
    recorded_at        = Column(DateTime, default=datetime.utcnow)

    shift = relationship("ShiftSession", back_populates="bps_logs")


class RingDetection(Base):
    """Network-level anomaly suppression."""
    __tablename__ = "ring_detections"
    id               = Column(Integer, primary_key=True, index=True)
    zone_id          = Column(String, index=True)
    activation_count = Column(Integer) # e.g. 20+
    new_to_zone_pct  = Column(Float)   # e.g. 60%+
    hold_active      = Column(Boolean, default=True)
    detected_at      = Column(DateTime, default=datetime.utcnow)
    hold_until       = Column(DateTime)


class BillingRecord(Base):
    """Tracks Monday auto-debits via Razorpay Mandates."""
    __tablename__ = "billing_records"
    id                  = Column(Integer, primary_key=True, index=True)
    worker_id           = Column(Integer, ForeignKey("workers.id"))
    plan_id             = Column(Integer, ForeignKey("plans.id"))
    amount              = Column(Float)
    razorpay_payment_id = Column(String, nullable=True)
    status              = Column(String, default="success") # success, failed, retrying
    billed_at           = Column(DateTime, default=datetime.utcnow)

    worker = relationship("Worker", back_populates="billing")


class PEBBaseline(Base):
    """AI Model output: Predicted Earning Baseline (PEB)."""
    __tablename__ = "peb_baselines"
    id                = Column(Integer, primary_key=True, index=True)
    worker_id         = Column(Integer, ForeignKey("workers.id"))
    day_of_week       = Column(String) # Mon, Tue...
    time_slot         = Column(String) # e.g. '18-22'
    zone_id           = Column(String)
    expected_earnings = Column(Float)
    computed_at       = Column(DateTime, default=datetime.utcnow)

    worker = relationship("Worker", back_populates="baselines")


class OTPSession(Base):
    """Temporary session for holding SMS/Twilio OTP state."""
    __tablename__ = "otp_sessions"
    id         = Column(Integer, primary_key=True, index=True)
    phone      = Column(String, index=True)
    otp_code   = Column(String)
    used       = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(minutes=10))


# ─── Legacy Aliases for Backwards Compatibility ───────────────────────────────
WorkerPlan    = Plan
PayoutRecord  = PayoutEvent
WeeklySummary = BillingRecord # Closest approximation for legacy code

# ─── Database Initialization ──────────────────────────────────────────────────

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
