"""
48-Hour SafarScore Forecast Engine
Uses Open-Meteo's hourly forecast to predict zone risk for the next 48 hours.
Feeds into worker 48-hr alert push notifications (Week 3 requirement).
"""
import httpx
import asyncio
from typing import List, Dict
from services.score_updater import SafarScoreAggregator


class ForecastEngine:
    """
    Fetches 48-hour weather forecast and generates hour-by-hour SafarScore predictions.
    """

    @staticmethod
    async def get_48hr_forecast(lat: float, lon: float, zone_name: str) -> Dict:
        """
        Calls Open-Meteo hourly forecast API (no key required).
        Returns list of predicted SafarScores for the next 48 hours.
        """
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&hourly=temperature_2m,rain,wind_speed_10m"
            f"&forecast_days=2&timezone=auto"
        )

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                res = await client.get(url)
                data = res.json()
        except Exception as e:
            return {"error": str(e), "zone": zone_name, "forecasts": []}

        hourly = data.get("hourly", {})
        times  = hourly.get("time", [])
        rain   = hourly.get("rain", [0] * len(times))
        wind   = hourly.get("wind_speed_10m", [0] * len(times))
        temp   = hourly.get("temperature_2m", [25] * len(times))

        forecasts = []
        peak_score = 0
        peak_time  = None

        for i, t in enumerate(times[:48]):
            env = {
                "rain_mm_hr": rain[i] if i < len(rain) else 0,
                "wind_kmh":   wind[i] if i < len(wind) else 0,
                "temp_c":     temp[i] if i < len(temp) else 25,
                "aqi":        60,  # Baseline AQI (no hourly AQI available free)
                "news_severity": 0
            }
            score_state = SafarScoreAggregator.compute_live_score(env)
            score = score_state["score"]

            forecasts.append({
                "time":    t,
                "score":   score,
                "level":   score_state["level"],
                "trigger": score_state["trigger"],
                "rain_mm": round(rain[i], 1) if i < len(rain) else 0
            })

            if score > peak_score:
                peak_score = score
                peak_time  = t

        # Build alert recommendation
        alert_windows = [f for f in forecasts if f["trigger"]]
        alert_msg = None
        if alert_windows:
            first_hit = alert_windows[0]["time"]
            alert_msg = (
                f"⚡ High-risk window expected around {first_hit}. "
                f"Peak SafarScore: {peak_score}/100. "
                f"Consider taking extra shifts before this window."
            )

        return {
            "zone":          zone_name,
            "forecast_hours": len(forecasts),
            "peak_score":    peak_score,
            "peak_time":     peak_time,
            "alert_windows": len(alert_windows),
            "worker_alert":  alert_msg,
            "forecasts":     forecasts
        }

    @staticmethod
    async def get_all_zones_48hr():
        """Fetch 48-hr forecast for all Bangalore zones in parallel."""
        ZONES = {
            "Koramangala":     (12.9352, 77.6245),
            "HSR Layout":      (12.9116, 77.6370),
            "JP Nagar":        (12.9050, 77.5850),
            "Indiranagar":     (12.9784, 77.6408),
            "Whitefield":      (12.9698, 77.7500),
            "Malleshwaram":    (13.0035, 77.5710),
            "Marathahalli":    (12.9591, 77.6974),
            "Electronic City": (12.8399, 77.6770),
        }
        tasks = [
            ForecastEngine.get_48hr_forecast(lat, lng, name)
            for name, (lat, lng) in ZONES.items()
        ]
        return await asyncio.gather(*tasks)
