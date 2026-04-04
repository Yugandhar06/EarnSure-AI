"""
SmartShift+ Weekly Premium Engine
Handles all billing cycle rules:
  - Monday auto-debit
  - Upgrade lockout logic
  - Downgrade rules (next Monday, no penalty)
  - Weekly summary generation
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from services.plan_recommender import PlanRecommender


class UpgradeLockoutError(Exception):
    pass


class PremiumEngine:
    """
    Governs all billing cycle rules for the weekly MicroShield plans.

    Billing Cycle Rules:
      MONDAY   -> Premium auto-debited. Coverage activates.
      DURING   -> Shift sessions counted against plan hour limit.
      SUNDAY   -> Weekly summary. Unused hours do NOT carry forward.
      UPGRADE  -> Only before Monday debit. BLOCKED if:
                    a) Within 6 hrs of predicted disruption (SafarScore >= 45)
                    b) After Monday 00:00 debit has fired for current week
      DOWNGRADE -> Anytime, effective next Monday, no penalty.
    """

    UPGRADE_LOCKOUT_HOURS = 6   # Lock upgrades 6hr before predicted disruption

    @staticmethod
    def can_upgrade(
        worker_id: str,
        current_plan_id: str,
        target_plan_id: str,
        zone_current_score: int,
        zone_alert_45_active: bool,
        monday_debit_fired_this_week: bool,
    ) -> Dict[str, Any]:
        """
        Evaluates whether a plan upgrade is allowed RIGHT NOW.

        Returns:
            allowed: bool
            reason:  str explaining the decision
        """
        plan_order = ["light", "regular", "standard", "pro", "max"]

        # Downgrade check (always allowed)
        if plan_order.index(target_plan_id) <= plan_order.index(current_plan_id):
            return {
                "allowed": True,
                "type": "downgrade",
                "effective": "Next Monday",
                "reason": "Downgrade allowed anytime. Effective next Monday. No penalty."
            }

        # Upgrade checks
        now = datetime.now()
        day_of_week = now.weekday()   # 0=Monday ... 6=Sunday

        # Rule 1: After Monday debit fires, no upgrade until next cycle
        if monday_debit_fired_this_week:
            return {
                "allowed": False,
                "type": "upgrade",
                "reason": "Monday billing already processed. Upgrade available from next Monday.",
                "fraud_note": "Prevent inflate-payout exploit: post-event tier switch blocked."
            }

        # Rule 2: Within 6hrs of predicted disruption (SafarScore alert_45 active)
        if zone_alert_45_active:
            return {
                "allowed": False,
                "type": "upgrade",
                "reason": f"Upgrade blocked — SafarScore {zone_current_score} triggered 48-hr disruption alert. "
                          f"Tier upgrades lock 6 hrs before predicted high-risk window.",
                "fraud_note": "Anti-fraud: last-minute tier-switch to inflate parametric payout blocked."
            }

        # Rule 3: All clear — upgrade allowed
        return {
            "allowed": True,
            "type": "upgrade",
            "effective": "Immediately",
            "reason": f"Upgrade from {current_plan_id} to {target_plan_id} approved."
        }

    @staticmethod
    def get_billing_cycle_status(worker_id: str) -> Dict[str, Any]:
        """
        Returns the current state of the worker's weekly billing cycle.
        """
        now = datetime.now()
        day_of_week = now.weekday()  # 0=Monday

        # How many days until next Monday
        days_to_monday = (7 - day_of_week) % 7 or 7
        next_monday = now + timedelta(days=days_to_monday)
        next_monday_at_6am = next_monday.replace(hour=6, minute=0, second=0, microsecond=0)

        # Coverage window
        if day_of_week == 0 and now.hour >= 6:
            cycle_start = now.replace(hour=6, minute=0, second=0, microsecond=0)
        else:
            last_monday = now - timedelta(days=day_of_week)
            cycle_start = last_monday.replace(hour=6, minute=0, second=0, microsecond=0)

        cycle_end = cycle_start + timedelta(days=7)

        return {
            "worker_id":          worker_id,
            "current_day":        now.strftime("%A"),
            "coverage_active":    True,
            "cycle_start":        cycle_start.isoformat(),
            "cycle_end":          cycle_end.isoformat(),
            "next_debit":         next_monday_at_6am.isoformat(),
            "hours_remaining_in_cycle": round((cycle_end - now).total_seconds() / 3600, 1),
            "upgrade_window_open":  day_of_week != 0,   # Closed on Monday after debit
            "summary_day":          "Sunday 8 PM",
            "unused_hours_carry_forward": False          # Explicitly per spec
        }

    @staticmethod
    def generate_weekly_summary(
        worker_id: str,
        plan_tier: str,
        premium_paid: float,
        total_payout_received: float,
        hours_covered: float,
        plan_max_hrs: int
    ) -> Dict[str, Any]:
        """
        Generates the Sunday 8PM weekly summary for a worker.
        """
        net_position = total_payout_received - premium_paid
        utilization = round((hours_covered / plan_max_hrs) * 100, 1) if plan_max_hrs else 0

        return {
            "worker_id":             worker_id,
            "week_ending":           datetime.now().strftime("%Y-%m-%d"),
            "plan":                  plan_tier,
            "premium_paid":          premium_paid,
            "total_payout_received": total_payout_received,
            "net_position":          round(net_position, 2),
            "hours_covered":         hours_covered,
            "plan_max_hrs":          plan_max_hrs,
            "utilization_pct":       utilization,
            "unused_hours":          max(0, plan_max_hrs - hours_covered),
            "carry_forward":         False,    # Per spec: unused hours do NOT carry forward
            "next_week_action":      "Auto-renew" if net_position >= 0 else "Consider upgrade",
            "message":               (
                f"Net position: Rs{net_position:+.0f} | "
                f"Coverage used: {utilization}% | "
                f"Unused hours reset on Monday."
            )
        }
