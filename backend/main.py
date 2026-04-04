import os
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from api.auth import router as auth_router
from api.billing import router as billing_router
from api.score import router as score_router
from services.cache import get_all_cached_zones
from database import init_db, SessionLocal, Worker, ShiftSession, PayoutEvent
import asyncio
import json
import datetime
import threading
import time
from api.admin import router as admin_router

# Load env
load_dotenv()

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SmartShift+ API", version="1.0")

@app.on_event("startup")
def startup():
    logger.info("[DB] Initializing database...")
    init_db()

# ================== MIDDLEWARE ==================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================== ROUTES ==================
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(billing_router, prefix="/api/billing", tags=["Billing"])
app.include_router(score_router, prefix="/api", tags=["Score & Payout"])
app.include_router(admin_router, prefix="/api", tags=["Admin"])

@app.get("/")
def read_root():
    return {"status": "SafarScore Engine Active"}

# ================== AUTO PAYOUT ENGINE ==================

from services.cache import get_cached_zone_score

def auto_trigger_payout(worker):
    db = SessionLocal()
    try:
        shift = db.query(ShiftSession).filter(
            ShiftSession.worker_id == worker.id,
            ShiftSession.ended_at == None
        ).first()

        if not shift:
            return

        zone_data = get_cached_zone_score(worker.zone)
        if not zone_data:
            return

        trigger = None

        if zone_data.get("score", 0) > 60:
            trigger = "risk"
        elif zone_data.get("rain_mm", 0) > 15:
            trigger = "rain"
        elif zone_data.get("temp_c", 0) > 43:
            trigger = "heat"

        if not trigger:
            return

        if shift.payout_triggered:
            return

        payout = PayoutEvent(
            worker_id=worker.id,
            shift_session_id=shift.id,
            payout_amount=400,
            status="paid",
            triggered_at=datetime.datetime.utcnow()
        )

        db.add(payout)
        shift.payout_triggered = True

        db.commit()

        print(f"💰 Payout triggered for {worker.worker_id} ({trigger})")

    finally:
        db.close()


def run_payout_engine():
    while True:
        db = SessionLocal()
        try:
            workers = db.query(Worker).all()
            for w in workers:
                auto_trigger_payout(w)
        finally:
            db.close()

        time.sleep(10)


# Start background thread
threading.Thread(target=run_payout_engine, daemon=True).start()

# ================== WEBSOCKET ==================

class ZoneScoreManager:
    def __init__(self):
        self.connections = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.connections.append(ws)

    async def disconnect(self, ws: WebSocket):
        if ws in self.connections:
            self.connections.remove(ws)

    async def broadcast(self, data: dict):
        for ws in self.connections:
            try:
                await ws.send_text(json.dumps(data))
            except:
                pass


zone_manager = ZoneScoreManager()


@app.websocket("/ws/zones")
async def websocket_zones(ws: WebSocket):
    await zone_manager.connect(ws)
    try:
        while True:
            zones = get_all_cached_zones()
            payload = {
                "zones": zones,
                "time": datetime.datetime.now().isoformat()
            }
            await ws.send_text(json.dumps(payload))
            await asyncio.sleep(15)
    except WebSocketDisconnect:
        await zone_manager.disconnect(ws)


@app.websocket("/ws/worker/{worker_id}")
async def websocket_worker(ws: WebSocket, worker_id: str):
    await ws.accept()
    try:
        while True:
            zones = get_all_cached_zones()
            zone_data = list(zones.values())[0] if zones else {"score": 20}

            await ws.send_text(json.dumps(zone_data))
            await asyncio.sleep(10)

    except WebSocketDisconnect:
        pass