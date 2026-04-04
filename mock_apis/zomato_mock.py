from mock_apis.swiggy_mock import generate_mock_earnings

def generate_zomato_earnings(worker_id: str, weeks: int = 8):
    """
    Generate mock hourly earning history for a Zomato gig worker.
    Re-uses base mock generator but tags platform explicitly.
    """
    return generate_mock_earnings(worker_id=worker_id, platform="zomato", weeks=weeks)
