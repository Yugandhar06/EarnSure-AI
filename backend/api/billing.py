from fastapi import APIRouter
from pydantic import BaseModel
import uuid

router = APIRouter()

class MandateRequest(BaseModel):
    plan_tier: str
    premium_amount: int

@router.post("/create-mandate")
def create_upi_mandate(req: MandateRequest):
    """
    Mocks a Razorpay UPI Autopay Mandate setup link creation
    """
    # In a real system, this hits `razorpay.Subscriptions.create()`
    mock_subscription_id = f"sub_{uuid.uuid4().hex[:14]}"
    mock_auth_link = f"https://sandbox.razorpay.com/upi/mandate/{mock_subscription_id}"
    
    return {
        "status": "success",
        "subscription_id": mock_subscription_id,
        "auth_link": mock_auth_link,
        "amount": req.premium_amount,
        "currency": "INR",
        "message": "UPI Mandate created for Monday 6 AM billing cycle"
    }

@router.post("/verify-mandate")
def verify_mandate(subscription_id: str):
    """
    Mock webhook/verification endpoint for the mandate.
    """
    return {
        "status": "active",
        "subscription_id": subscription_id,
        "message": "Coverage is now ACTIVE"
    }
