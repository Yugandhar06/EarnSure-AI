from fastapi import APIRouter

router = APIRouter()

@router.get("/admin/overview")
def get_overview():
    return {
        "workers": {
            "total": 120,
            "active_plans": 85
        },
        "plans": {
            "tier_distribution": {
                "Light": 20,
                "Regular": 35,
                "Standard": 25,
                "Pro": 15,
                "Max": 5
            },
            "weekly_revenue_inr": 840000
        },
        "payouts": {
            "total_inr": 250000,
            "approved_total": 60
        },
        "fraud": {
            "flagged_alerts": 7
        }
    }

@router.get("/admin/payout_feed")
def payout_feed():
    return {
        "payouts": [
            {
                "name": "Rajesh Kumar",
                "zone": "HSR Layout",
                "amt": 400,
                "time": "2 min ago"
            },
            {
                "name": "Amit Singh",
                "zone": "Koramangala",
                "amt": 250,
                "time": "5 min ago"
            }
        ]
    }

@router.get("/admin/fraud_feed")
def fraud_feed():
    return {
        "alerts": [
            {
                "title": "GPS Spoofing Detected",
                "meta": "W-99821",
                "detail": "Worker showed zero GPS variance — flagged as spoof"
            },
            {
                "title": "Suspicious Pattern",
                "meta": "W-11223",
                "detail": "Repeated payout attempts in short interval"
            }
        ]
    }