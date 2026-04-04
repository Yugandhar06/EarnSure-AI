from typing import Dict, Any, List

class PlanRecommender:
    """
    Handles the Weekly Premium Pricing Engine for SmartShift+.
    Final Premium = Base Plan Rate × Zone Risk Multiplier × Claim History Factor
    """

    BASE_PLANS = [
        {"id": "light", "tier": "Light", "max_hrs": 15, "base_premium": 99, "coverage_ratio": 0.60, "max_payout": 1000, "desc": "Up to 15 hrs/week"},
        {"id": "regular", "tier": "Regular", "max_hrs": 35, "base_premium": 179, "coverage_ratio": 0.65, "max_payout": 2000, "desc": "Up to 35 hrs/week"},
        {"id": "standard", "tier": "Standard", "max_hrs": 55, "base_premium": 249, "coverage_ratio": 0.70, "max_payout": 3500, "desc": "Up to 55 hrs/week"},
        {"id": "pro", "tier": "Pro", "max_hrs": 70, "base_premium": 349, "coverage_ratio": 0.80, "max_payout": 5000, "desc": "Up to 70 hrs/week"},
        {"id": "max", "tier": "Max", "max_hrs": 168, "base_premium": 449, "coverage_ratio": 0.90, "max_payout": 7000, "desc": "Unlimited hours"}
    ]

    ZONE_MULTIPLIERS = {
        "low": 0.9,      # Low risk discount
        "medium": 1.0,   # Standard risk
        "high": 1.15,    # High risk markup
        "extreme": 1.3   # Extreme risk markup
    }

    CLAIM_MULTIPLIERS = {
        "zero_claims": 0.9,      # Loyalty discount
        "clean_approved": 1.0,   # Status quo
        "one_flagged": 1.1,      # Penalty
        "multiple_flagged": 1.2  # Max penalty
    }

    @classmethod
    def generate_plan_offerings(cls, worker_hours_per_week: int, zone_risk: str = "medium", claim_history: str = "zero_claims") -> Dict[str, Any]:
        """
        Generates the 5 plan tiers customized for the specific worker's history,
        and identifies the optimal recommended plan based on their OAuth hours.
        """
        z_mult = cls.ZONE_MULTIPLIERS.get(zone_risk.lower(), 1.0)
        c_mult = cls.CLAIM_MULTIPLIERS.get(claim_history.lower(), 1.0)

        offerings = []
        recommended_plan_id = "standard" # Default fallback

        for plan in cls.BASE_PLANS:
            # The core mathematical formula
            final_premium = int(round(plan["base_premium"] * z_mult * c_mult))
            
            offerings.append({
                "id": plan["id"],
                "tier": plan["tier"],
                "final_premium_inr": final_premium,
                "base_premium_inr": plan["base_premium"],
                "coverage_ratio_percent": int(plan["coverage_ratio"] * 100),
                "max_coverage_inr": plan["max_payout"],
                "description": plan["desc"]
            })

            # AI Logic: Find the plan that best fits their historical hours
            # Attempt to use KMeans clustering model instead of hardcoded rules
            try:
                import os, joblib, numpy as np
                model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'models', 'kmeans_plan_recommender.joblib')
                kmeans = joblib.load(model_path)
                
                # Mock historical metrics for feature input: [weekly_hours, avg_safar_score, claims_history]
                claims_numeric = 0.0 if claim_history == "zero_claims" else 1.0
                score_numeric = 50.0 if zone_risk == "medium" else 75.0
                
                X = np.array([[worker_hours_per_week, score_numeric, claims_numeric]])
                cluster_idx = kmeans.predict(X)[0]
                
                # Center indexing logic (Clusters 0 to 4 correspond to the 5 tiers)
                # Since KMeans doesn't guarantee order mapping, we lazily sort cluster centers by hours!
                centers = kmeans.cluster_centers_[:, 0] # Extract the hours column
                # Get the rank of this specific cluster ID
                ordered_ranks = np.argsort(centers)
                tier_index = np.where(ordered_ranks == cluster_idx)[0][0]
                
                recommended_plan_id = cls.BASE_PLANS[tier_index]["id"]
            except Exception as e:
                # Fallback to rules if file missing
                if worker_hours_per_week <= plan["max_hrs"] and recommended_plan_id == "standard":
                    if worker_hours_per_week > (plan["max_hrs"] - 20): 
                       recommended_plan_id = plan["id"]
                if worker_hours_per_week > 70:
                    recommended_plan_id = "max"

        return {
            "worker_hours_profile": worker_hours_per_week,
            "multipliers_applied": {
                "zone_risk": z_mult,
                "claim_history": c_mult
            },
            "recommended_plan_id": recommended_plan_id,
            "plans": offerings
        }

# Wrapper for legacy compatibility during refactor
def recommend_plan(baseline_data: dict, zone_risk="medium", claim_history="zero_claims"):
    # Mocking standard hours from baseline if purely mocked DB
    hours = baseline_data.get("total_slots_worked", 30) // 8 # Rough week estimation
    return PlanRecommender.generate_plan_offerings(hours, zone_risk, claim_history)
