"""
SmartShift+ Push Notification Service
Firebase Cloud Messaging (FCM) with graceful fallback to console logging.

Covers:
  - 48-hr advance alert when SafarScore alert_45 fires
  - Payout approved notification
  - Sunday weekly summary notification
  - TrustMesh fraud block alert (to admin)

FCM_SERVER_KEY environment variable controls live/demo mode.
"""
import os
import json
import logging
from typing import Optional, List

log = logging.getLogger(__name__)

FCM_SERVER_KEY = os.getenv("FCM_SERVER_KEY", "")
FCM_URL = "https://fcm.googleapis.com/fcm/send"

# ── Demo mode: log to console if no FCM key ───────────────────────────────
DEMO_MODE = not bool(FCM_SERVER_KEY)
if DEMO_MODE:
    log.info("[FCM] No FCM_SERVER_KEY set — running in DEMO mode (notifications logged only)")


class FCMNotificationService:
    """
    Sends Firebase Cloud Messaging push notifications.
    Falls back gracefully to console logging when FCM key is absent.
    """

    @staticmethod
    def _send(token: str, title: str, body: str, data: dict = None) -> dict:
        """Core FCM send — HTTP POST to FCM endpoint."""
        payload = {
            "to": token,
            "notification": {"title": title, "body": body},
            "data": data or {},
            "android": {"priority": "high"},
            "apns": {"headers": {"apns-priority": "10"}}
        }

        if DEMO_MODE:
            log.info(f"[FCM DEMO] TO={token[:20]}... | {title} | {body}")
            return {"success": True, "mode": "demo", "title": title, "body": body}

        try:
            import httpx
            headers = {
                "Authorization": f"key={FCM_SERVER_KEY}",
                "Content-Type": "application/json"
            }
            resp = httpx.post(FCM_URL, headers=headers,
                              content=json.dumps(payload), timeout=5)
            result = resp.json()
            if result.get("success") == 1:
                log.info(f"[FCM] Sent: {title} -> {token[:20]}...")
            else:
                log.warning(f"[FCM] Failed: {result}")
            return result
        except Exception as e:
            log.error(f"[FCM] Error: {e}")
            return {"success": False, "error": str(e)}

    # ── Notification types ─────────────────────────────────────────────────

    @classmethod
    def send_zone_alert_45(
        cls,
        fcm_token: str,
        worker_name: str,
        zone: str,
        score: int,
        forecast_hours: int = 48
    ) -> dict:
        """
        48-hr advance alert: SafarScore crossed 45.
        Tier upgrade window closes. Workers should prepare.
        """
        return cls._send(
            token=fcm_token,
            title=f"SmartShift+ Alert: {zone} Risk Rising",
            body=(
                f"Hi {worker_name}, SafarScore in {zone} is {score}/100. "
                f"High disruption likely in next {forecast_hours} hours. "
                f"Plan upgrade window closes soon."
            ),
            data={
                "type": "zone_alert_45",
                "zone": zone,
                "score": str(score),
                "action": "open_forecast"
            }
        )

    @classmethod
    def send_payout_approved(
        cls,
        fcm_token: str,
        worker_name: str,
        amount: float,
        eta: str = "< 30 minutes"
    ) -> dict:
        """Payout approved — money on the way."""
        return cls._send(
            token=fcm_token,
            title="SmartShift+ Payout Approved!",
            body=(
                f"Hi {worker_name}, your payout of Rs{amount:.0f} "
                f"has been approved. Money arrives in {eta} via UPI."
            ),
            data={
                "type": "payout_approved",
                "amount": str(amount),
                "action": "open_payouts"
            }
        )

    @classmethod
    def send_weekly_summary(
        cls,
        fcm_token: str,
        worker_name: str,
        premium_paid: float,
        payout_received: float,
        net_position: float
    ) -> dict:
        """Sunday 8PM weekly summary push."""
        net_str = f"+Rs{net_position:.0f}" if net_position >= 0 else f"-Rs{abs(net_position):.0f}"
        return cls._send(
            token=fcm_token,
            title="Your SmartShift+ Weekly Summary",
            body=(
                f"Hi {worker_name}! This week: Premium paid Rs{premium_paid:.0f} | "
                f"Payout received Rs{payout_received:.0f} | Net {net_str}"
            ),
            data={
                "type": "weekly_summary",
                "net": str(net_position),
                "action": "open_summary"
            }
        )

    @classmethod
    def send_bps_soft_flag(
        cls,
        fcm_token: str,
        worker_name: str
    ) -> dict:
        """BPS 50-74 soft flag — reassure worker, 10-min fast track."""
        return cls._send(
            token=fcm_token,
            title="Claim Under Verification (10 min)",
            body=(
                f"Hi {worker_name} — we're verifying your claim. "
                f"This is NOT your fault. Your payout will NOT be reduced."
            ),
            data={"type": "bps_soft_flag", "action": "open_claim_status"}
        )

    @classmethod
    def send_ring_alert_worker(
        cls,
        fcm_token: str,
        worker_name: str,
        zone: str
    ) -> dict:
        """Zone-wide hold — reassure honest worker, Rs75 credit promised."""
        return cls._send(
            token=fcm_token,
            title="Zone Under Verification (Up to 2 hrs)",
            body=(
                f"Hi {worker_name} — unusual activity detected near {zone}. "
                f"Our team will contact you within 2 hours. "
                f"Approved claims receive full payout + Rs75 credit."
            ),
            data={"type": "ring_hold", "zone": zone, "credit": "75",
                  "action": "open_claim_status"}
        )

    @classmethod
    def send_batch_zone_alerts(
        cls,
        workers: List[dict],  # List of {fcm_token, name, zone, score}
    ) -> dict:
        """
        Batch send zone alert_45 notifications to all workers in at-risk zones.
        Called by scheduler when 15-min refresh detects score crossing 45.
        """
        sent = 0
        failed = 0
        for w in workers:
            result = cls.send_zone_alert_45(
                fcm_token=w.get("fcm_token", "demo_token"),
                worker_name=w.get("name", "Worker"),
                zone=w.get("zone", "Your Zone"),
                score=w.get("score", 45)
            )
            if result.get("success"):
                sent += 1
            else:
                failed += 1
        return {"sent": sent, "failed": failed, "total": len(workers)}
