import httpx
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ExternalAPIClient:
    """
    Handles live external data ingestion for the SafarScore engine.
    Uses free Open-Meteo for Weather/AQI to avoid API Key friction in the demo,
    and falls back gracefully if premium Google/News API keys aren't added to .env.
    """
    
    @staticmethod
    async def fetch_weather_and_aqi(lat: float, lon: float) -> Dict[str, float]:
        """
        Hyper-local rainfall and AQI monitoring.
        Prioritizes OpenWeatherMap (if API Key in .env), falls back to Open-Meteo (Keyless).
        """
        api_key = os.getenv("OPENWEATHER_API_KEY")
        results = {"rain_mm_hr": 0.0, "temp_c": 25.0, "wind_kmh": 0.0, "aqi": 50.0}

        async with httpx.AsyncClient() as client:
            try:
                if api_key and api_key != "0a3ce84cb23a40f21ba1c39e931291f1": # Skip if it matches the generic placeholder in some examples
                    # 1. OpenWeatherMap Call (Premium)
                    # Note: OWM OneCall 3.0 or Current Weather API
                    owm_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
                    aqi_url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={api_key}"
                    
                    import asyncio
                    w_res, a_res = await asyncio.gather(client.get(owm_url), client.get(aqi_url))
                    
                    if w_res.status_code == 200:
                        w_data = w_res.json()
                        results["temp_c"] = w_data.get("main", {}).get("temp", 25.0)
                        results["wind_kmh"] = w_data.get("wind", {}).get("speed", 0.0) * 3.6 # m/s to km/h
                        # OWM provides 1h or 3h rain. We use 1h if available.
                        results["rain_mm_hr"] = w_data.get("rain", {}).get("1h", 0.0)
                        
                        if a_res.status_code == 200:
                            a_data = a_res.json()
                            # OWM AQI is 1-5 (Good, Fair, Moderate, Poor, Very Poor)
                            # Indian standard equivalent: 1->50, 2->100, 3->200, 4->300, 5->500
                            idx = a_data.get("list", [{}])[0].get("main", {}).get("aqi", 2)
                            mapping = {1: 50, 2: 120, 3: 220, 4: 340, 5: 480}
                            results["aqi"] = mapping.get(idx, 100)
                            
                        return results # Success with Premium OWM

                # 2. Open-Meteo Fallback (Keyless / Default)
                weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,rain,wind_speed_10m&timezone=auto"
                aqi_url = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}&current=european_aqi&timezone=auto"

                import asyncio
                weather_res, aqi_res = await asyncio.gather(client.get(weather_url), client.get(aqi_url))

                w_data = weather_res.json()
                a_data = aqi_res.json()

                if "current" in w_data:
                    results["rain_mm_hr"] = w_data["current"]["rain"]
                    results["temp_c"] = w_data["current"]["temperature_2m"]
                    results["wind_kmh"] = w_data["current"]["wind_speed_10m"]
                
                if "current" in a_data:
                    results["aqi"] = a_data["current"]["european_aqi"] * 2.5

            except Exception as e:
                logger.error(f"External API Fetch Error: {e}")
        
        return results

    @staticmethod
    async def fetch_news_alerts(zone_name: str) -> int:
        """
        Simulates fetching from NewsAPI / spaCy keyword matching.
        Uses real HTTP requests if key exists, otherwise falls back.
        Returns a 0-100 severity score for local news disruptions.
        """
        api_key = os.getenv("NEWS_API_KEY")
        if not api_key:
            return 0 # Normal, no alerts detected

        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(
                    f"https://newsapi.org/v2/everything?q={zone_name}+AND+(strike+OR+flood+OR+protest)",
                    headers={"X-Api-Key": api_key}
                )
                data = res.json()
                if data.get("totalResults", 0) > 3:
                    return 85 # High severity news event
                return 10
        except:
            return 0
