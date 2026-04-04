import razorpay
import os
import uuid
from typing import Dict, Any

# For hackathons, if environment variables aren't set, we fall back to a mock flow 
# to ensure the demo continues seamlessly even without live API credentials.
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "rzp_test_MOCK_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "MOCK_SECRET")

# Initialize Razorpay Client
try:
    client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
except Exception:
    client = None

class RazorpayEngine:
    """
    Handles UPI Autopay Mandates (Weekly Premiums) and UPI Instant Payouts (Claims)
    """

    @staticmethod
    def create_weekly_subscription(worker_id: str, plan_name: str, premium_amount_inr: float) -> Dict[str, Any]:
        """
        Creates a UPI Autopay mandate for the worker's weekly premium shift deduction.
        """
        # Razorpay takes amounts in base subunits (Paisa)
        amount_paisa = int(premium_amount_inr * 100)
        
        # MOCK FALLBACK FOR DEMOS IF KEYS ARE UNAVAILABLE
        if RAZORPAY_KEY_ID == "rzp_test_MOCK_KEY_ID" or not client:
            return {
                "status": "success",
                "payment_mode": "UPI Autopay Simulator",
                "razorpay_subscription_id": f"sub_mock_{uuid.uuid4().hex[:8]}",
                "amount_inr": premium_amount_inr,
                "notes": f"Weekly recurring mapped to {plan_name}"
            }

        try:
            # 1. Create a Plan dynamically or fetch existing
            # (In production, Plans are pre-created on Razorpay dashboard)
            
            # 2. Create the Subscription (UPI Mandate)
            subscription_data = {
                "plan_id": "plan_real_id_here", # Hardcoded for demo
                "total_count": 52,             # 1 Year of weeks
                "quantity": 1,
                "customer_notify": 1,
                "notes": {"worker_id": worker_id}
            }
            sub = client.subscription.create(data=subscription_data)
            
            return {
                "status": "success",
                "payment_mode": "UPI Autopay (Live Sandbox)",
                "razorpay_subscription_id": sub["id"],
                "amount_inr": premium_amount_inr,
                "short_url": sub.get("short_url") # Link for worker to complete mandate
            }
        except Exception as e:
            return {"status": "error", "detail": str(e)}

    @staticmethod
    def initiate_instant_payout(worker_id: str, payout_amount_inr: float) -> Dict[str, Any]:
        """
        Calculates and instantly transfers gap-coverage money into the Worker's linked UPI account.
        RazorpayX Payouts Sandbox.
        """
        amount_paisa = int(payout_amount_inr * 100)
        
        if RAZORPAY_KEY_ID == "rzp_test_MOCK_KEY_ID" or not client:
            return {
                "status": "processed",
                "razorpay_payout_id": f"pout_mock_{uuid.uuid4().hex[:8]}",
                "amount_inr": payout_amount_inr,
                "speed": "IMPS / UPI",
                "eta": "< 30 seconds"
            }
            
        try:
            # RazorpayX API call
            payout_data = {
                "account_number": "2323230043890252", # RazorpayX Current Account (Sandbox)
                "fund_account_id": "fa_sandbox_worker", # Looked up from DB
                "amount": amount_paisa,
                "currency": "INR",
                "mode": "UPI",
                "purpose": "payout",
                "queue_if_low_balance": True,
                "reference_id": f"claim_{uuid.uuid4().hex[:8]}",
                "narration": "SmartShift MicroShield Payout"
            }
            
            payout = client.payout.create(data=payout_data)
            
            return {
                "status": payout["status"],
                "razorpay_payout_id": payout["id"],
                "amount_inr": payout_amount_inr,
                "speed": payout["mode"]
            }
        except Exception as e:
            return {"status": "error", "detail": str(e)}
