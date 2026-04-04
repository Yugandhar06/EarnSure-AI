from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import SessionLocal, Worker, Plan, ShiftSession, PayoutEvent
from services.cache import get_all_cached_zones, get_cached_zone_score, cache_zone_score
from datetime import datetime, timedelta

def auto_trigger_payout(worker):
    db = SessionLocal()
    try:
        # check active shift
        shift = db.query(ShiftSession).filter(
            ShiftSession.worker_id == worker.id,
            ShiftSession.ended_at == None
        ).first()

        if not shift:
            return

        zone_data = get_cached_zone_score(worker.zone)

        if not zone_data:
            return

        # 🔥 3 triggers
        trigger = None

        if zone_data["score"] > 60:
            trigger = "risk"
        elif zone_data.get("rain_mm", 0) > 15:
            trigger = "rain"
        elif zone_data.get("temp_c", 0) > 43:
            trigger = "heat"

        if not trigger:
            return


        # prevent duplicate payout
        existing = db.query(PayoutEvent).filter(
            PayoutEvent.shift_session_id == shift.id
        ).first()

        if existing:
            return
\
        payout = PayoutEvent(
            worker_id=worker.id,
            shift_session_id=shift.id,   # 🔥 ADD THIS LINE
            payout_amount=400,
            status="paid",
            triggered_at=datetime.utcnow()
        )

        db.add(payout)

        # ✅ mark shift as triggered
        shift.payout_triggered = True

        db.commit()

    finally:
        db.close()


def calculate_premium(score):
    if score <= 30:
        return 3
    elif score <= 60:
        return 5
    elif score <= 80:
        return 7
    else:
        return 9


router = APIRouter()

# ==============================
# DEMO TRIGGER
# ==============================
class DemoTriggerRequest(BaseModel):
    scenario: str
    zone_id: str = "Koramangala"

@router.post("/demo/trigger")
def update_demo_scenario(req: DemoTriggerRequest):
    zone = req.zone_id
    cached = get_cached_zone_score(zone) or {
        "score": 28, "level": "LOW RISK", "trigger": False
    }

    scen = req.scenario.lower()
    if scen == 'rain':
        cached.update({"score": 72, "level": "HIGH RISK", "trigger": True})
    elif scen == 'flood':
        cached.update({"score": 94, "level": "SEVERE", "trigger": True})
    elif scen == 'spoofer':
        cached.update({"score": 45, "level": "MODERATE", "trigger": False})
    else:
        cached.update({"score": 28, "level": "LOW RISK", "trigger": False})

    cache_zone_score(zone, cached)
    return {"status": "success", "zone": zone, "new_state": cached}


# ==============================
# ADMIN ZONE RISK
# ==============================
@router.get("/admin/zone_risk")
def get_zone_risk():
    cached = get_all_cached_zones()
    if not cached:
        return {"zones": []}

    return {"zones": [
        {"name": name, **data} for name, data in cached.items()
    ]}

@router.get("/worker/dashboard_details")
def get_worker_dashboard_details(worker_id: str):
    db = SessionLocal()
    try:
        worker = db.query(Worker).filter(Worker.worker_id == worker_id).first()

        if not worker:
            raise HTTPException(status_code=404, detail="Worker not found")

        plan = db.query(Plan).filter(
            Plan.worker_id == worker.id,
            Plan.active == True
        ).first()

        zone_name = worker.zone or "Koramangala"

        # ✅ FIX: define BEFORE dictionary
        zone_data = get_cached_zone_score(zone_name) or {
            "score": 28, "level": "LOW RISK", "trigger": False
        }

        active_shift = db.query(ShiftSession).filter(
            ShiftSession.worker_id == worker.id,
            ShiftSession.ended_at == None
        ).first()

        payouts = db.query(PayoutEvent).filter(
            PayoutEvent.worker_id == worker.id
        ).order_by(PayoutEvent.triggered_at.desc()).limit(10).all()

        payouts_list = [{
            "amount": p.payout_amount,
            "time": p.triggered_at.strftime("%b %d, %I:%M %p"),
            "status": p.status,
            "icon": "💸"
        } for p in payouts]

        return {
            "worker": {
                "id": worker.worker_id,
                "phone": worker.phone,
                "name": worker.name,
                "zone": zone_name,
                "trust_score": worker.trust_score
            },
            "plan": {
                "tier": plan.tier if plan else "None",
                "premium": calculate_premium(zone_data["score"]),
                "max_hours": plan.covered_hrs_per_week if plan else 40,
                "coverage_ratio": plan.coverage_ratio if plan else 0.7,
                "max_payout": plan.max_payout if plan else 1000
            },
            "shift": {
                "active": active_shift is not None,
                "id": active_shift.id if active_shift else None,
                "started_at": active_shift.started_at.isoformat() if active_shift else None,
                "hours_used": active_shift.hours_used if active_shift else 0
            },
            "billing": {
                "current_day": datetime.now().strftime("%A"),
                "next_debit": (
                    datetime.now() + timedelta(days=(7 - datetime.now().weekday()))
                ).replace(hour=6, minute=0, second=0).isoformat()
            },
            "weekly_summary": {
                "hours_covered": 12.5,
                "max_hours": 40,
                "premium_paid": plan.final_weekly_premium if plan else 150,
                "total_payout_received": sum(
                    p.payout_amount for p in payouts if p.status == "paid"
                )
            },
            "safar_score": zone_data,
            "recent_events": payouts_list
        }

    finally:
        db.close()


# ==============================
# PAYOUTS
# ==============================
@router.get("/worker/payouts")
def get_worker_payouts(worker_id: str):
    db = SessionLocal()
    try:
        worker = db.query(Worker).filter(Worker.worker_id == worker_id).first()

        if not worker:
            raise HTTPException(status_code=404, detail="Worker not found")

        payouts = db.query(PayoutEvent).filter(
            PayoutEvent.worker_id == worker.id
        ).order_by(PayoutEvent.triggered_at.desc()).all()

        return {
            "status": "success",
            "payouts": [
                {
                    "amount": p.payout_amount,
                    "status": p.status,
                    "time": p.triggered_at.isoformat()
                }
                for p in payouts
            ]
        }

    finally:
        db.close()


# ==============================
# ✅ FIXED SHIFT START (IMPORTANT)
# ==============================
class ShiftStartRequest(BaseModel):
    worker_id: str
    zone_id: str

@router.post("/worker/shift/start")
def start_shift(req: ShiftStartRequest):
    db = SessionLocal()
    try:
        worker = db.query(Worker).filter(
            Worker.worker_id == req.worker_id
        ).first()

        if not worker:
            raise HTTPException(404, "Worker not found")

        plan = db.query(Plan).filter(
            Plan.worker_id == worker.id,
            Plan.active == True
        ).first()

        if not plan:
            raise HTTPException(400, "No active plan")

        new_shift = ShiftSession(
            worker_id=worker.id,
            plan_id=plan.id,
            zone_id=req.zone_id,
            started_at=datetime.utcnow()
        )

        db.add(new_shift)
        db.commit()

        return {"status": "success", "shift_id": new_shift.id}

    finally:
        db.close()


# ==============================
# SHIFT END
# ==============================
class ShiftEndRequest(BaseModel):
    shift_id: int

@router.post("/worker/shift/end")
def end_shift(req: ShiftEndRequest):
    db = SessionLocal()
    try:
        shift = db.query(ShiftSession).filter(
            ShiftSession.id == req.shift_id
        ).first()

        if not shift:
            raise HTTPException(404, "Shift not found")

        shift.ended_at = datetime.utcnow()
        duration = (shift.ended_at - shift.started_at).total_seconds() / 3600
        shift.hours_used = round(duration, 1)

        db.commit()

        return {"status": "success", "duration": shift.hours_used}

    finally:
        db.close()