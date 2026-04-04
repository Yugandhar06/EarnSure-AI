import os
from typing import Dict, Any

class SMSService:
    """
    Unified SMS & OTP Engine. 
    REMOVED TWILIO: Now uses Console Simulation for safety.
    """

    def __init__(self):
        self.client = None
        print("[AUTH] SMS Service initialized in SIMULATION mode.")

    def send_otp(self, phone: str, otp: str = "123456") -> Dict[str, Any]:
        """Always simulate OTP sending via console."""
        # Normalize phone for India default (if no +)
        if not phone.startswith("+"):
            phone = f"+91{phone}"

        print(f"[{'!' * 10}] SMS SIMULATION MODE [{'!' * 10}]")
        print(f"   Target Phone: {phone}")
        print(f"   OTP Code    : {otp}")
        print(f"   Message     : Your SmartShift+ Security Code is: {otp}")
        print(f"[{'!' * 10}] SMS SIMULATION MODE [{'!' * 10}]")

        return {
            "status": "success",
            "mode": "Simulation (Console Out)",
            "message": "OTP printed to terminal.",
            "target": phone
            # "otp" intentionally omitted — never send raw OTP over network
        }

    def check_otp(self, phone: str, otp: str) -> bool:
        """Always return true in mock mode (validation happens in DB session)."""
        return True

# Singleton instance
sms_service = SMSService()
