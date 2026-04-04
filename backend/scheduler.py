"""
SmartShift+ Background Scheduler
Simulates Celery behaviour using Python's schedule + threading.
Runs 3 background jobs:
  1. Monday 9AM  — Bill all active workers (debit weekly premium)
  2. Every 15min — Refresh all zone SafarScores from Open-Meteo
  3. Sunday 6PM  — Send weekly earnings summary to all workers
"""
import schedule
import threading
import time
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [SCHEDULER] %(message)s")
log = logging.getLogger(__name__)


# ─── Job 1: Monday Billing ──────────────────────────────────────────────────
def run_monday_billing():
    log.info("=== MONDAY BILLING JOB STARTED ===")
    try:
        import sys, os
        sys.path.insert(0, os.path.dirname(__file__))
        from database import SessionLocal, Worker, WorkerPlan
        from services.payment_gateway import RazorpayEngine

        db = SessionLocal()
        try:
            # Get all active plans
            active_plans = db.query(WorkerPlan).filter(WorkerPlan.active == True).all()
            billed = 0
            for plan in active_plans:
                worker = db.query(Worker).filter(Worker.id == plan.worker_id).first()
                if not worker:
                    continue
                result = RazorpayEngine.create_weekly_subscription(
                    worker_id=worker.worker_id,
                    plan_name=plan.plan_tier,
                    premium_amount_inr=plan.final_premium
                )
                log.info(f"  Billed {worker.worker_id} ({plan.plan_tier}) "
                         f"Rs{plan.final_premium} → {result.get('razorpay_subscription_id','mock')}")
                billed += 1
            log.info(f"=== BILLING COMPLETE: {billed} workers billed ===")
        finally:
            db.close()
    except Exception as e:
        log.error(f"Billing job failed: {e}")


# ─── Job 2: 15-min SafarScore Zone Refresh ──────────────────────────────────
def run_zone_risk_refresh():
    log.info("--- Zone SafarScore Refresh ---")
    try:
        import asyncio
        import sys, os
        sys.path.insert(0, os.path.dirname(__file__))
        from services.external_apis import ExternalAPIClient
        from services.score_updater import SafarScoreAggregator

        # Bangalore zone GPS coordinates
        ZONES = {
            "Koramangala":    (12.9352, 77.6245),
            "HSR Layout":     (12.9116, 77.6370),
            "JP Nagar":       (12.9050, 77.5850),
            "Indiranagar":    (12.9784, 77.6408),
            "Whitefield":     (12.9698, 77.7500),
            "Malleshwaram":   (13.0035, 77.5710),
            "Marathahalli":   (12.9591, 77.6974),
            "Yelahanka":      (13.1007, 77.5963),
            "Electronic City":(12.8399, 77.6770),
        }

        async def refresh_all():
            for zone_name, (lat, lng) in ZONES.items():
                try:
                    env_data = await ExternalAPIClient.fetch_weather_and_aqi(lat, lng)
                    news     = await ExternalAPIClient.fetch_news_alerts(zone_name)
                    env_data["news_severity"] = news
                    score_state = SafarScoreAggregator.compute_live_score(env_data)
                    score_state["lat"]  = lat
                    score_state["lng"]  = lng

                    # Persist to Redis/in-memory cache (15-min TTL)
                    from services.cache import cache_zone_score
                    cache_zone_score(zone_name, score_state)

                    log.info(f"  {zone_name}: {score_state['score']}/100 ({score_state['level']})")

                    # Fire FCM push if score just crossed alert_45 threshold
                    if score_state.get("alert_45"):
                        from services.notifications import FCMNotificationService
                        from database import SessionLocal, Worker
                        db = SessionLocal()
                        try:
                            workers_in_zone = db.query(Worker).filter(
                                Worker.zone == zone_name,
                                Worker.kyc_verified == True
                            ).all()
                            batch = [
                                {"fcm_token": getattr(w, "fcm_token", "demo_token"),
                                 "name": w.name or "Worker",
                                 "zone": zone_name,
                                 "score": score_state['score']}
                                for w in workers_in_zone
                            ]
                            if batch:
                                result = FCMNotificationService.send_batch_zone_alerts(batch)
                                log.info(f"  FCM alerts sent: {result}")
                        finally:
                            db.close()

                except Exception as e:
                    log.warning(f"  {zone_name}: refresh failed — {e}")

        asyncio.run(refresh_all())
        log.info("--- Zone refresh complete ---")
    except Exception as e:
        log.error(f"Zone refresh job failed: {e}")


# ─── Job 3: Sunday Summary ──────────────────────────────────────────────────
def run_sunday_summary():
    log.info("=== SUNDAY WEEKLY SUMMARY ===")
    try:
        import sys, os
        sys.path.insert(0, os.path.dirname(__file__))
        from database import SessionLocal, Worker, WorkerPlan

        db = SessionLocal()
        try:
            workers = db.query(Worker).filter(Worker.kyc_verified == True).all()
            log.info(f"  Generating summaries for {len(workers)} workers...")
            from services.notifications import FCMNotificationService
            for w in workers:
                plan = db.query(WorkerPlan).filter(
                    WorkerPlan.worker_id == w.id,
                    WorkerPlan.active == True
                ).first()
                plan_info = f"{plan.plan_tier} (Rs{plan.final_premium}/week)" if plan else "No active plan"
                log.info(f"  [{w.worker_id}] {w.name or 'Unknown'} — Zone: {w.zone} — Plan: {plan_info}")

                # Send FCM weekly summary push
                if plan:
                    FCMNotificationService.send_weekly_summary(
                        fcm_token=getattr(w, "fcm_token", "demo_token"),
                        worker_name=w.name or "Worker",
                        premium_paid=float(plan.final_premium),
                        payout_received=0.0,   # In production: query payout history
                        net_position=-float(plan.final_premium)
                    )
        finally:
            db.close()
    except Exception as e:
        log.error(f"Sunday summary job failed: {e}")


# ─── Scheduler Loop ─────────────────────────────────────────────────────────
def start_scheduler():
    log.info("SmartShift+ Scheduler starting...")

    # Monday 9AM billing
    schedule.every().monday.at("09:00").do(run_monday_billing)

    # Zone refresh every 15 minutes
    schedule.every(15).minutes.do(run_zone_risk_refresh)

    # Sunday 6PM weekly summary
    schedule.every().sunday.at("18:00").do(run_sunday_summary)

    # Run zone refresh immediately on startup
    run_zone_risk_refresh()

    log.info("Scheduler active. Jobs registered:")
    log.info("  → Monday 09:00 — Weekly Billing")
    log.info("  → Every 15 min — Zone SafarScore Refresh")
    log.info("  → Sunday 18:00 — Worker Summary")

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    start_scheduler()
