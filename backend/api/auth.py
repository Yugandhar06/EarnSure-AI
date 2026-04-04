import sys, os
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_path)

from database import get_db, Worker, OTPSession, WorkerPlan
from auth_utils import generate_worker_id, generate_otp, create_jwt, get_current_worker
from mock_apis.swiggy_mock import generate_mock_earnings as get_swiggy
from mock_apis.zomato_mock import generate_zomato_earnings as get_zomato
from services.peb_engine import peb_engine
from services.plan_recommender import PlanRecommender, recommend_plan
from services.payment_gateway import RazorpayEngine

router = APIRouter()

# ─── Pydantic Schemas ─────────────────────────────────────

class PhoneLogin(BaseModel):
    phone: str

class OTPVerify(BaseModel):
    phone: str
    otp: str

class KYCSubmit(BaseModel):
    phone: str
    name: str
    aadhaar: str
    zone: str

class PlatformLink(BaseModel):
    platform: str
    zone_risk: str = "medium"
    claim_history: str = "zero_claims"

class PlanActivate(BaseModel):
    plan_id: str  # light/regular/standard/pro/max

# ─── Routes ───────────────────────────────────────────────

from services.sms_service import sms_service

# ─── Pydantic Schemas ─────────────────────────────────────
# ... (rest of previous schemas)

@router.post("/otp/send")
def send_otp(req: PhoneLogin, db: Session = Depends(get_db)):
    """Step 1 — Send OTP to phone. Creates OTP record in DB. Uses Twilio for real SMS."""
    otp = generate_otp()  # Mock code to keep internal logic clean
    
    # 1. Trigger Twilio (or Console Fallback)
    dispatch = sms_service.send_otp(req.phone, otp)
    
    # 2. Store in DB (invalidate previous)
    db.query(OTPSession).filter(OTPSession.phone == req.phone, OTPSession.used == False).update({"used": True})
    db.add(OTPSession(phone=req.phone, otp_code=otp))
    db.commit()
    
    return {
        "status": "success",
        "message": f"OTP sent to {req.phone}",
        "gateway": dispatch["mode"],
        "id": dispatch["status"],
        "mock_otp": otp if dispatch["mode"] != "Twilio Verify API" else "*******"
    }


@router.post("/otp/verify")
def verify_otp(req: OTPVerify, db: Session = Depends(get_db)):
    """Step 2 — Verify OTP, create/login Worker, return JWT."""
    # Check OTP
    otp_record = db.query(OTPSession).filter(
        OTPSession.phone == req.phone,
        OTPSession.otp_code == req.otp,
        OTPSession.used == False
    ).order_by(OTPSession.id.desc()).first()

    if not otp_record:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    # Mark OTP used
    otp_record.used = True
    db.commit()

    # Get or create Worker
    worker = db.query(Worker).filter(Worker.phone == req.phone).first()
    if not worker:
        worker = Worker(phone=req.phone, worker_id=generate_worker_id())
        db.add(worker)
        db.commit()
        db.refresh(worker)
        is_new = True
    else:
        is_new = False

    token = create_jwt(worker.worker_id, worker.phone)

    return {
        "status": "success",
        "token": token,
        "worker_id": worker.worker_id,
        "is_new_registration": is_new,
        "kyc_verified": worker.kyc_verified
    }


@router.post("/kyc/submit")
def submit_kyc(req: KYCSubmit, db: Session = Depends(get_db), current: dict = Depends(get_current_worker)):
    """Step 3 — Submit Aadhaar KYC. Protected by JWT."""
    worker = db.query(Worker).filter(Worker.worker_id == current["sub"]).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    worker.name = req.name
    worker.aadhaar = req.aadhaar[:4] + "XXXXXXXX"  # Mask aadhaar for storage
    worker.zone = req.zone
    worker.kyc_verified = True
    db.commit()

    return {"status": "success", "kyc_verified": True, "name": req.name, "zone": req.zone}


@router.post("/oauth/link")
def link_platform(req: PlatformLink, db: Session = Depends(get_db), current: dict = Depends(get_current_worker)):
    """Step 4 — Link platform, run PEB engine, return all plan options."""
    worker = db.query(Worker).filter(Worker.worker_id == current["sub"]).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    worker.platform = req.platform
    worker.zone_risk = req.zone_risk
    worker.claim_history = req.claim_history
    db.commit()

    # Run earnings analysis
    if req.platform.lower() == "swiggy":
        data = get_swiggy(worker.worker_id)
    else:
        data = get_zomato(worker.worker_id)

    baseline = peb_engine.train_baseline(data)
    hours = baseline.get("total_slots_worked", 0) // 8
    plan_data = PlanRecommender.generate_plan_offerings(hours, req.zone_risk, req.claim_history)

    return {
        "status": "success",
        "platform": req.platform,
        "earnings_analyzed_hours": len(data),
        "baseline": baseline,
        "recommended_plan": plan_data
    }


@router.post("/plan/activate")
def activate_plan(req: PlanActivate, db: Session = Depends(get_db), current: dict = Depends(get_current_worker)):
    """Final Step — Worker selects & activates a plan. Deactivates previous, stores new in DB."""
    worker = db.query(Worker).filter(Worker.worker_id == current["sub"]).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    # Deactivate existing plans
    db.query(WorkerPlan).filter(WorkerPlan.worker_id == worker.id, WorkerPlan.active == True).update({"active": False})

    # Find the plan config
    all_plans = PlanRecommender.generate_plan_offerings(
        40, worker.zone_risk or "medium", worker.claim_history or "zero_claims"
    )
    chosen = next((p for p in all_plans["plans"] if p["id"] == req.plan_id), None)
    if not chosen:
        raise HTTPException(status_code=400, detail="Invalid plan ID")

    z_mult = all_plans["multipliers_applied"]["zone_risk"]
    c_mult = all_plans["multipliers_applied"]["claim_history"]

    new_plan = WorkerPlan(
        worker_id=worker.id,
        tier=chosen.get("name", "standard"),
        plan_tier=chosen.get("tier", "Standard"),
        final_premium=chosen.get("final_premium_inr", 249.0),
        final_weekly_premium=chosen.get("final_premium_inr", 249.0),
        base_premium=chosen.get("base_premium_inr", 249.0),
        coverage_ratio=chosen.get("coverage_ratio_percent", 70.0) / 100,
        max_payout=chosen.get("max_coverage_inr", 3500.0),
        zone_multiplier=z_mult,
        claim_multiplier=c_mult
    )
    worker.active_plan = chosen.get("tier", "Standard")
    db.add(new_plan)
    db.commit()
    db.refresh(new_plan)

    # Trigger Razorpay Subscription
    payment_info = RazorpayEngine.create_weekly_subscription(
        worker_id=worker.worker_id,
        plan_name=chosen["tier"],
        premium_amount_inr=chosen["final_premium_inr"]
    )

    return {
        "status": "success",
        "message": f"{chosen['tier']} plan activated successfully",
        "plan": chosen,
        "payment_mandate": payment_info,
        "activated_at": new_plan.activated_at.isoformat(),
        "worker_id": worker.worker_id
    }


@router.get("/me")
def get_my_profile(db: Session = Depends(get_db), current: dict = Depends(get_current_worker)):
    """Protected route — returns full worker profile + active plan."""
    worker = db.query(Worker).filter(Worker.worker_id == current["sub"]).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    active_plan = db.query(WorkerPlan).filter(
        WorkerPlan.worker_id == worker.id, WorkerPlan.active == True
    ).order_by(WorkerPlan.id.desc()).first()

    return {
        "worker_id": worker.worker_id,
        "phone": worker.phone,
        "name": worker.name,
        "zone": worker.zone,
        "platform": worker.platform,
        "kyc_verified": worker.kyc_verified,
        "zone_risk": worker.zone_risk,
        "claim_history": worker.claim_history,
        "active_plan": {
            "plan_id": active_plan.id,
            "tier": active_plan.plan_tier,
            "premium": active_plan.final_premium,
            "max_payout": active_plan.max_payout,
            "coverage_ratio": active_plan.coverage_ratio,
            "activated_at": active_plan.activated_at.isoformat()
        } if active_plan else None
    }
