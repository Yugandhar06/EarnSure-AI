"""
TrustMesh — Fraud & Anti-Spoofing Defense
Full implementation per SmartShift+ spec section 9.

Covers:
  - BPS 6-sub-signal evaluation (ML IsolationForest)
  - 4-tier BPS decision engine (auto / soft-flag / hard-flag / rejected)
  - Ring Detection (Telegram syndicate pattern)
  - API Fallback for Signal 1 when primary source is down
  - Disruption threshold validation
  - Veteran leniency rule (BPS threshold -25 when zone_score >= 80)
  - 75 INR inconvenience credit for honest flagged workers
  - ParametricPayoutEngine (3-signal + Dynamic Effort Rule)
"""

import os
import joblib
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, List, Optional
from collections import defaultdict

# ── In-memory ring detection store ─────────────────────────────────────────
# In production this would be Redis with TTL
_zone_activations: Dict[str, List[dict]] = defaultdict(list)
_ring_alerts: Dict[str, datetime] = {}


# ═══════════════════════════════════════════════════════════════════════════
# DISRUPTION THRESHOLD VALIDATOR
# ═══════════════════════════════════════════════════════════════════════════

class DisruptionThresholds:
    """
    Spec-defined thresholds that qualify an event as a real external disruption.
    Used for Signal 1 validation.
    """

    THRESHOLDS = {
        "rain_mm_hr":   15.0,    # mm/hr — Heavy rainfall
        "temp_c_max":   43.0,    # Celsius — Extreme heat
        "aqi":          300.0,   # CPCB hazardous AQI
        "wind_kmh":     65.0,    # km/h — Severe storm
        "flood_alert":  1,       # Boolean — IMD flood alert issued
    }

    DISRUPTION_LABELS = {
        "rain_mm_hr":   "Heavy rainfall (>{threshold}mm/hr)",
        "temp_c_max":   "Extreme heat (>{threshold}C + govt advisory)",
        "aqi":          "Hazardous AQI (>{threshold})",
        "wind_kmh":     "Severe storm wind (>{threshold}km/h)",
        "flood_alert":  "IMD flood alert issued",
    }

    @classmethod
    def evaluate_signal_1(
        cls,
        live_env: Dict[str, float],
        news_keywords: List[str] = None,
        zone_score: int = 0,
        zone_score_baseline: float = 35.0,  # 12-week rolling average
        peer_reports_zero_orders: int = 0,  # Number of workers in zone with 0 orders
        peer_count: int = 0
    ) -> Dict[str, Any]:
        """
        Evaluates Signal 1 with full API fallback chain:
          Primary:  Live weather/AQI exceeds threshold
          Fallback1: News NLP keyword match (flood, strike, curfew)
          Fallback2: Historical anomaly (score > 2-sigma deviation from baseline)
          Fallback3: Peer-network — multiple workers reporting zero orders

        Real disruptions are NEVER blocked by API downtime.
        """
        triggers = []
        source_used = "none"

        # ── Primary: Check live sensor thresholds ─────────────────────────
        rain = live_env.get("rain_mm_hr", 0)
        if rain >= cls.THRESHOLDS["rain_mm_hr"]:
            triggers.append(f"Heavy rain: {rain}mm/hr (threshold: {cls.THRESHOLDS['rain_mm_hr']}mm)")

        temp = live_env.get("temp_c", 25)
        if temp >= cls.THRESHOLDS["temp_c_max"]:
            triggers.append(f"Extreme heat: {temp}C (threshold: {cls.THRESHOLDS['temp_c_max']}C)")

        aqi = live_env.get("aqi", 0)
        if aqi >= cls.THRESHOLDS["aqi"]:
            triggers.append(f"Hazardous AQI: {aqi} (threshold: {cls.THRESHOLDS['aqi']})")

        flood = live_env.get("flood_alert", 0)
        if flood >= 1:
            triggers.append("IMD Flood Alert issued")

        if triggers:
            source_used = "primary_weather_api"

        # ── Fallback 1: News NLP keyword match ───────────────────────────
        if not triggers and news_keywords:
            DISRUPTION_KEYWORDS = {
                "flood", "flooding", "waterlogging", "inundation",
                "strike", "bandh", "curfew", "protest", "shutdown",
                "cyclone", "storm", "landslide", "hailstorm"
            }
            matched = [k for k in news_keywords if k.lower() in DISRUPTION_KEYWORDS]
            if matched:
                triggers.append(f"News NLP match: {matched}")
                source_used = "news_nlp_fallback"

        # ── Fallback 2: Historical anomaly (>2-sigma deviation) ──────────
        if not triggers and zone_score > 0:
            # 2-sigma: mean + 2 * std_dev. With baseline 35, std ~12 → threshold ~59
            sigma_threshold = zone_score_baseline + (2 * 12.0)
            if zone_score >= sigma_threshold:
                triggers.append(
                    f"Historical anomaly: score {zone_score} is >{sigma_threshold:.0f} "
                    f"(2-sigma above {zone_score_baseline:.0f} baseline)"
                )
                source_used = "historical_anomaly_fallback"

        # ── Fallback 3: Peer network — multiple workers reporting zero orders ─
        if not triggers and peer_count > 3:
            peer_zero_pct = (peer_reports_zero_orders / peer_count) * 100
            if peer_zero_pct >= 60:
                triggers.append(
                    f"Peer network: {peer_reports_zero_orders}/{peer_count} workers "
                    f"({peer_zero_pct:.0f}%) reporting zero orders"
                )
                source_used = "peer_network_fallback"

        confirmed = len(triggers) > 0
        return {
            "signal_1_confirmed": confirmed,
            "source": source_used,
            "triggers": triggers,
            "severity": (
                "Extreme" if zone_score >= 80
                else "High" if zone_score >= 61
                else "None"
            ),
            "api_fallback_used": source_used != "primary_weather_api" and confirmed
        }


# ═══════════════════════════════════════════════════════════════════════════
# TRUSTMESH BPS ENGINE
# ═══════════════════════════════════════════════════════════════════════════

class TrustMeshEngine:
    """
    Behavioral Presence Score (BPS) — 6 sub-signals.
    Replaces raw GPS with a composite that cannot be entirely faked.
    """

    # BPS Decision Tiers — exact per spec section 9
    BPS_TIERS = [
        (75, 100, "auto",      "Signal 2 CONFIRMED — Auto-payout < 30 min"),
        (50,  74, "soft_flag", "Soft flag — 10-minute fast-track verification"),
        (25,  49, "hard_flag", "Hard flag — 2-hour human review"),
        (0,   24, "rejected",  "Hard block — Logged, claim rejected"),
    ]

    INCONVENIENCE_CREDIT_INR = 75  # Paid to flagged-but-honest workers on approval

    @staticmethod
    def evaluate_bps(worker_data: Dict[str, Any]) -> Tuple[int, str]:
        """
        Returns (bps_score, rationale).
        Uses IsolationForest ML model; falls back to rule engine on error.
        """
        try:
            model_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "models", "isolation_forest_bps.joblib"
            )
            iso_forest = joblib.load(model_path)

            X = np.array([[
                1.0 if worker_data.get("mock_location_flag", False) else 0.05,
                worker_data.get("gps_variance_std", 5.0),
                2.5 if worker_data.get("accelerometer_active", True) else 0.1,
                0.9 if worker_data.get("speed_kmh", 15) < 80 else 0.2,
                worker_data.get("orders_last_4_hrs", 1) * 35,
            ]])

            pred = iso_forest.predict(X)[0]
            if pred == -1:
                return 15, "Hard Block: ML Detected Anomaly (Syndicate Spoofer Signature)"
            else:
                return 92, "Genuine Location Signature (ML Verified)"

        except Exception:
            # Rule-based fallback
            if worker_data.get("mock_location_flag", False):
                return 0, "Hard Block: Mock Location Flag Detected"
            score = 80
            if not worker_data.get("accelerometer_active", True): score -= 20
            if worker_data.get("gps_variance_std", 5.0) < 0.5:   score -= 20
            if worker_data.get("orders_last_4_hrs", 1) == 0:      score -= 20
            return max(0, score), "Rule-Based Fallback (ML model unavailable)"

    @classmethod
    def get_bps_decision(
        cls,
        bps_score: int,
        zone_score: int = 65,
        is_veteran: bool = False
    ) -> Dict[str, Any]:
        """
        Converts raw BPS into a routing decision per spec tiers.
        Veteran leniency: if zone_score >= 80, effective threshold drops 25 pts.
        """
        effective_bps = bps_score
        leniency_applied = False

        # Veteran leniency rule (spec: "Score >80 + veteran → BPS threshold -25pts")
        if zone_score >= 80 and is_veteran:
            effective_bps = min(100, bps_score + 25)
            leniency_applied = True

        for low, high, tier, message in cls.BPS_TIERS:
            if low <= effective_bps <= high:
                result = {
                    "tier":              tier,
                    "raw_bps":           bps_score,
                    "effective_bps":     effective_bps,
                    "signal_2_status":   "confirmed" if tier == "auto" else "flagged" if tier in ("soft_flag", "hard_flag") else "rejected",
                    "message":           message,
                    "leniency_applied":  leniency_applied,
                    "auto_payout":       tier == "auto",
                }
                # Add worker-facing UX message per spec
                if tier == "soft_flag":
                    result["worker_message"] = (
                        "Verifying your claim — ~10 minutes. "
                        "This is NOT your fault. Your payout will NOT be reduced."
                    )
                    result["inconvenience_credit_inr"] = cls.INCONVENIENCE_CREDIT_INR
                elif tier == "hard_flag":
                    result["worker_message"] = (
                        "Our team contacts you within 2 hours. "
                        "Approved claims receive full payout + Rs75 credit."
                    )
                    result["inconvenience_credit_inr"] = cls.INCONVENIENCE_CREDIT_INR
                elif tier == "rejected":
                    result["worker_message"] = (
                        "This claim could not be verified. "
                        "If you believe this is an error, contact support."
                    )
                return result

        return {"tier": "rejected", "raw_bps": bps_score, "signal_2_status": "rejected"}


# ═══════════════════════════════════════════════════════════════════════════
# RING DETECTION ENGINE
# ═══════════════════════════════════════════════════════════════════════════

class RingDetectionEngine:
    """
    Catches Telegram syndicate patterns — 20+ simultaneous zone activations
    with >60% having no prior zone history.
    """

    ACTIVATION_THRESHOLD  = 20    # Minimum activations in 15 min to trigger scan
    NEW_WORKER_PCT_TRIGGER = 0.60  # 60% new-to-zone = probable ring
    HOLD_HOURS            = 2     # Hours to hold all claims in zone

    @classmethod
    def record_activation(cls, zone_id: str, worker_id: str, has_zone_history: bool):
        """Log a shift activation for ring detection analysis."""
        _zone_activations[zone_id].append({
            "worker_id":       worker_id,
            "timestamp":       datetime.now(),
            "has_zone_history": has_zone_history,
        })
        # Purge stale entries older than 15 minutes
        cutoff = datetime.now() - timedelta(minutes=15)
        _zone_activations[zone_id] = [
            a for a in _zone_activations[zone_id] if a["timestamp"] > cutoff
        ]

    @classmethod
    def check_ring(cls, zone_id: str) -> Dict[str, Any]:
        """
        Evaluates whether recent activations in this zone constitute a ring.
        Returns ring_detected flag + recommended action.
        """
        recent = _zone_activations.get(zone_id, [])
        total  = len(recent)

        if total < cls.ACTIVATION_THRESHOLD:
            return {
                "ring_detected": False,
                "zone_id":       zone_id,
                "activations_15min": total,
                "threshold":     cls.ACTIVATION_THRESHOLD,
                "message":       f"Normal activity ({total} activations, threshold {cls.ACTIVATION_THRESHOLD})"
            }

        new_to_zone = [w for w in recent if not w["has_zone_history"]]
        new_pct     = len(new_to_zone) / total

        if new_pct >= cls.NEW_WORKER_PCT_TRIGGER:
            # RING DETECTED
            _ring_alerts[zone_id] = datetime.now()
            return {
                "ring_detected":      True,
                "zone_id":            zone_id,
                "activations_15min":  total,
                "new_to_zone_count":  len(new_to_zone),
                "new_to_zone_pct":    round(new_pct * 100, 1),
                "action":             "zone_wide_hold",
                "hold_hours":         cls.HOLD_HOURS,
                "legitimate_worker_credit_inr": 75,
                "message": (
                    f"RING ALERT: {total} activations in 15min, "
                    f"{new_pct*100:.0f}% new-to-zone. "
                    f"All claims paused {cls.HOLD_HOURS}hrs. "
                    f"Legitimate workers fast-tracked with Rs75 credit."
                )
            }

        return {
            "ring_detected": False,
            "zone_id":       zone_id,
            "activations_15min": total,
            "new_to_zone_pct": round(new_pct * 100, 1),
            "message":       f"Elevated activity but new-worker % below threshold ({new_pct*100:.0f}%)"
        }

    @classmethod
    def is_zone_on_hold(cls, zone_id: str) -> bool:
        """Returns True if zone has an active ring hold."""
        alert_time = _ring_alerts.get(zone_id)
        if not alert_time:
            return False
        return (datetime.now() - alert_time).total_seconds() < (cls.HOLD_HOURS * 3600)


# ═══════════════════════════════════════════════════════════════════════════
# PARAMETRIC PAYOUT ENGINE
# ═══════════════════════════════════════════════════════════════════════════

class ParametricPayoutEngine:
    """
    3-Signal Validation Engine + Dynamic Effort Rule.
    Payout = (PEB - Actual) * Coverage Ratio * Signal Confidence
    """

    @staticmethod
    def process_claim(
        event_severity: str,
        worker_bps: int,
        platform_demand_dropped: bool,
        peb_weekly: float,
        actual_earned: float,
        coverage_ratio: float = 0.70,
        zone_score: int = 65,
        orders_in_shift: int = 1,
        is_veteran: bool = False,
        zone_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Full pipeline:
          1. Zone-wide ring hold check
          2. Dynamic Effort Rule
          3. Signal 1 (mandatory) + Signal 2 (BPS) + Signal 3 (demand)
          4. Payout math
        """

        # ── Ring hold check ──────────────────────────────────────────
        if zone_id and RingDetectionEngine.is_zone_on_hold(zone_id):
            return {
                "status":  "held",
                "reason":  f"Zone {zone_id} is under ring-pattern hold (up to 2 hrs). "
                           f"Your claim is queued. Legitimate workers receive Rs75 credit.",
                "inconvenience_credit_inr": 75,
                "payout":  0
            }

        # ── Dynamic Effort Rule ───────────────────────────────────────
        if zone_score >= 80:
            min_orders_required = 0
            effort_rule = "Extreme: GPS presence only (0 orders)"
        elif zone_score >= 75 and is_veteran:
            min_orders_required = 0
            effort_rule = "Veteran leniency: 0 orders required (score>=75)"
        elif zone_score >= 61:
            min_orders_required = 1
            effort_rule = "High risk: 1 order minimum required"
        else:
            return {"status": "rejected", "reason": "SafarScore below trigger threshold (60)", "payout": 0}

        if orders_in_shift < min_orders_required:
            return {
                "status": "rejected",
                "reason": f"Dynamic Effort Rule: need {min_orders_required} order(s), got {orders_in_shift}.",
                "effort_rule": effort_rule,
                "payout": 0
            }

        # ── Signal 1: External Event (mandatory) ─────────────────────
        signal_1 = event_severity in ["High", "Extreme"]
        if not signal_1:
            return {
                "status": "rejected",
                "reason": "Signal 1 (External Event) MANDATORY — not confirmed.",
                "payout": 0
            }

        # ── Signal 2: BPS Decision Tier ──────────────────────────────
        bps_decision = TrustMeshEngine.get_bps_decision(worker_bps, zone_score, is_veteran)
        bps_tier     = bps_decision["tier"]

        # Spec: "BPS never directly rejects a payout" — low BPS triggers review, not auto-reject
        signal_2        = bps_tier in ("auto", "soft_flag", "hard_flag")
        signal_2_weight = 1.0 if bps_tier == "auto" else 0.9 if bps_tier == "soft_flag" else 0.75

        # ── Signal 3: Zone Demand Drop >40% ──────────────────────────
        signal_3 = platform_demand_dropped

        confirmed_signals = 1  # Signal 1
        if signal_2: confirmed_signals += 1
        if signal_3: confirmed_signals += 1

        if confirmed_signals < 2:
            return {
                "status":            "flagged",
                "reason":            f"Only 1/3 signals confirmed (BPS={worker_bps}). Queued for review.",
                "bps_decision":      bps_decision,
                "signals_confirmed": 1,
                "payout":            0
            }

        # ── Confidence + Payout Math ──────────────────────────────────
        confidence_ratio = 1.0 if confirmed_signals == 3 else 0.85
        income_gap       = peb_weekly - actual_earned

        if income_gap <= 0:
            return {"status": "rejected", "reason": "Worker earned above PEB — no gap.", "payout": 0}

        # Apply BPS resolution delay if soft/hard flag
        if bps_tier == "soft_flag":
            status = "pending_fast_track"
            eta    = "~10 minutes"
            credit = TrustMeshEngine.INCONVENIENCE_CREDIT_INR
        elif bps_tier == "hard_flag":
            status = "pending_review"
            eta    = "~2 hours"
            credit = TrustMeshEngine.INCONVENIENCE_CREDIT_INR
        else:
            status = "approved"
            eta    = "< 30 minutes"
            credit = 0

        calculated_payout = round(income_gap * coverage_ratio * confidence_ratio, 2)

        return {
            "status":                status,
            "payout_amount":         calculated_payout,
            "signals_confirmed":     confirmed_signals,
            "confidence":            confidence_ratio,
            "bps_score":             worker_bps,
            "bps_tier":              bps_tier,
            "bps_decision":          bps_decision,
            "coverage_ratio":        coverage_ratio,
            "zone_score":            zone_score,
            "effort_rule_applied":   effort_rule,
            "eta":                   eta,
            "inconvenience_credit":  credit,
            "message": (
                f"Payout: Rs{calculated_payout} | "
                f"Signals: {confirmed_signals}/3 | "
                f"BPS: {worker_bps}/100 ({bps_tier}) | "
                f"ETA: {eta}"
            )
        }
