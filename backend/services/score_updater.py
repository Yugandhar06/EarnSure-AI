from typing import Dict, Any

class SafarScoreAggregator:
    """
    10-signal SafarScore aggregator (0-100).
    Weights sum to 1.0.  Score 100 = all 10 signals at maximum risk simultaneously.

    Defaults are ZERO for all signals — a perfectly clear, calm day scores near 0.
    Callers (scheduler, fetch-live) pass live signal values from APIs.
    """

    WEIGHTS = {
        "rainfall":        0.20,
        "aqi":             0.15,
        "platform_demand": 0.15,
        "traffic":         0.10,
        "temperature":     0.10,
        "news_strikes":    0.10,
        "historical_risk": 0.05,
        "wind":            0.05,
        "seasonal":        0.05,
        "flood_alert":     0.05,
    }

    @classmethod
    def compute_live_score(cls, live_data: Dict[str, float]) -> Dict[str, Any]:
        """
        Converts live environmental + platform data into 0-100 risk score.
        Missing signals default to 0 (clean baseline — no artificial floor).
        """
        score   = 0.0
        details = {}

        # Signal 1: Rainfall (mm/hr) — 20mm/hr = full risk
        rain = live_data.get("rain_mm_hr", live_data.get("rain_mm", 0))
        rain_risk = min(100, (rain / 20.0) * 100)
        score += rain_risk * cls.WEIGHTS["rainfall"]
        details["rain"] = f"{rain} mm/hr (Risk: {int(rain_risk)})"

        # Signal 2: AQI — 200 AQI = full risk (default 0 = clean air)
        aqi = live_data.get("aqi", 0)
        aqi_risk = min(100, (aqi / 200.0) * 100)
        score += aqi_risk * cls.WEIGHTS["aqi"]
        details["aqi"] = f"{int(aqi)} AQI (Risk: {int(aqi_risk)})"

        # Signal 3: Platform Demand Drop — inferred from rain if not provided
        demand_drop = live_data.get("demand_drop_pct", 0)
        if demand_drop == 0 and rain > 15:
            demand_drop = min(80, rain * 2)
        demand_risk = min(100, (demand_drop / 50.0) * 100)
        score += demand_risk * cls.WEIGHTS["platform_demand"]
        details["demand"] = f"{int(demand_drop)}% drop (Risk: {int(demand_risk)})"

        # Signal 4: Traffic Congestion — inferred from rain if not provided
        traffic = live_data.get("traffic_congestion", 0)
        if traffic == 0 and rain > 10:
            traffic = min(80, rain * 1.8)
        traffic_risk = min(100, traffic)
        score += traffic_risk * cls.WEIGHTS["traffic"]
        details["traffic"] = f"Congestion risk: {int(traffic_risk)}"

        # Signal 5: Temperature extreme (>40C or <15C in India)
        temp = live_data.get("temp_c", 25)
        temp_risk = 0
        if temp > 40:   temp_risk = min(100, (temp - 40) * 20)
        elif temp < 15: temp_risk = min(100, (15 - temp) * 10)
        score += temp_risk * cls.WEIGHTS["temperature"]
        details["temp"] = f"{temp}C (Risk: {int(temp_risk)})"

        # Signal 6: News/Strike/Curfew — string or numeric
        news_raw = live_data.get("news_severity", 0)
        NEWS_MAP = {"none": 0, "low": 15, "medium": 40, "high": 70, "extreme": 95}
        news_risk = NEWS_MAP.get(news_raw.lower(), 0) if isinstance(news_raw, str) else float(news_raw)
        score += min(100, news_risk) * cls.WEIGHTS["news_strikes"]
        details["news"] = f"Severity: {news_raw} (Risk: {int(news_risk)})"

        # Signal 7: Historical disruption data (default 0 = no prior events)
        hist_risk = live_data.get("historical_risk", 0)
        score += min(100, hist_risk) * cls.WEIGHTS["historical_risk"]

        # Signal 8: Wind speed (km/h) — 50km/h = full risk
        wind = live_data.get("wind_kmh", 0)
        wind_risk = min(100, (wind / 50.0) * 100)
        score += wind_risk * cls.WEIGHTS["wind"]
        details["wind"] = f"{wind} km/h (Risk: {int(wind_risk)})"

        # Signal 9: Seasonal baseline (0=dry, 20=monsoon, 40=peak monsoon)
        seasonal = live_data.get("seasonal_risk", 0)
        score += min(100, seasonal) * cls.WEIGHTS["seasonal"]

        # Signal 10: Flood alert (auto-inferred from extreme rain)
        flood_alert = live_data.get("flood_alert", 0)
        if flood_alert == 0 and rain > 25:
            flood_alert = min(100, (rain - 25) * 5)
        score += min(100, flood_alert) * cls.WEIGHTS["flood_alert"]
        details["flood"] = f"Flood alert: {int(flood_alert)}"

        # Final bounds + spec-compliant score bands
        final_score = int(max(0, min(100, score)))

        if final_score > 80:
            level = "Extreme"; color = "Black"; payout_eligible = True; min_orders = 0
        elif final_score > 60:
            level = "High";    color = "Red";   payout_eligible = True; min_orders = 1
        elif final_score > 30:
            level = "Medium";  color = "Yellow"; payout_eligible = False; min_orders = None
        else:
            level = "Low";     color = "Green";  payout_eligible = False; min_orders = None

        # Key threshold flags
        alert_45 = final_score >= 45  # 48-hr alert + tier upgrade window closes
        trigger  = final_score > 60   # Payout trigger
        leniency = final_score >= 75  # Veteran leniency rule
        extreme  = final_score >= 80  # GPS-presence-only zone

        return {
            "score":            final_score,
            "level":            level,
            "color":            color,
            "trigger":          trigger,
            "payout_eligible":  payout_eligible,
            "min_orders":       min_orders,
            "alert_45":         alert_45,
            "leniency_75":      leniency,
            "extreme_80":       extreme,
            "api_metrics_used": details
        }
