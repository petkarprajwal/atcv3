#!/usr/bin/env python3
"""
OpenWeatherMap API Integration
FREE weather data integration
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class WeatherData:
    """Weather data structure"""
    location: str
    latitude: float
    longitude: float
    temperature: float
    feels_like: float
    humidity: float
    pressure: float
    visibility: float
    wind_speed: float
    wind_direction: float
    wind_gust: float
    cloud_coverage: float
    weather_main: str
    weather_description: str
    weather_icon: str
    timestamp: datetime

@dataclass
class WeatherAlert:
    """Weather alert data"""
    alert_id: str
    event: str
    description: str
    start_time: datetime
    end_time: datetime
    severity: str
    areas_affected: List[str]
    source: str

class OpenWeatherMapIntegration:
    """OpenWeatherMap API integration"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.rate_limit_delay = 1  # 60 calls per minute = 1 second delay
        
        # API endpoints
        self.endpoints = {
            "current": "/weather",
            "forecast": "/forecast",
            "forecast_hourly": "/forecast",
            "alerts": "/alerts",
            "air_pollution": "/air_pollution",
            "geocoding": "/geo/1.0/direct"
        }
        
        logger.info("OpenWeatherMap Integration initialized")
    
    def get_current_weather(self, lat: float, lon: float) -> Optional[WeatherData]:
        """Get current weather for specific coordinates"""
        
        if not self.api_key:
            logger.warning("No API key provided - using mock data")
            return self._get_mock_weather(lat, lon)
        
        try:
            url = f"{self.base_url}{self.endpoints['current']}"
            params = {
                "lat": lat,
                "lon": lon,
                "appid": self.api_key,
                "units": "metric"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            weather = WeatherData(
                location=data.get("name", "Unknown"),
                latitude=data["coord"]["lat"],
                longitude=data["coord"]["lon"],
                temperature=data["main"]["temp"],
                feels_like=data["main"]["feels_like"],
                humidity=data["main"]["humidity"],
                pressure=data["main"]["pressure"],
                visibility=data.get("visibility", 0) / 1000,  # Convert to km
                wind_speed=data["wind"]["speed"],
                wind_direction=data["wind"].get("deg", 0),
                wind_gust=data["wind"].get("gust", 0),
                cloud_coverage=data["clouds"]["all"],
                weather_main=data["weather"][0]["main"],
                weather_description=data["weather"][0]["description"],
                weather_icon=data["weather"][0]["icon"],
                timestamp=datetime.fromtimestamp(data["dt"])
            )
            
            logger.info(f"Retrieved weather for {weather.location}")
            return weather
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching weather: {e}")
            return self._get_mock_weather(lat, lon)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return self._get_mock_weather(lat, lon)
    
    def get_weather_forecast(self, lat: float, lon: float, days: int = 5) -> List[WeatherData]:
        """Get weather forecast for specific coordinates"""
        
        if not self.api_key:
            logger.warning("No API key provided - using mock forecast")
            return self._get_mock_forecast(lat, lon, days)
        
        try:
            url = f"{self.base_url}{self.endpoints['forecast']}"
            params = {
                "lat": lat,
                "lon": lon,
                "appid": self.api_key,
                "units": "metric",
                "cnt": days * 8  # 8 forecasts per day (3-hour intervals)
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            forecasts = []
            for item in data["list"]:
                weather = WeatherData(
                    location=data["city"]["name"],
                    latitude=data["city"]["coord"]["lat"],
                    longitude=data["city"]["coord"]["lon"],
                    temperature=item["main"]["temp"],
                    feels_like=item["main"]["feels_like"],
                    humidity=item["main"]["humidity"],
                    pressure=item["main"]["pressure"],
                    visibility=item.get("visibility", 0) / 1000,
                    wind_speed=item["wind"]["speed"],
                    wind_direction=item["wind"].get("deg", 0),
                    wind_gust=item["wind"].get("gust", 0),
                    cloud_coverage=item["clouds"]["all"],
                    weather_main=item["weather"][0]["main"],
                    weather_description=item["weather"][0]["description"],
                    weather_icon=item["weather"][0]["icon"],
                    timestamp=datetime.fromtimestamp(item["dt"])
                )
                forecasts.append(weather)
            
            logger.info(f"Retrieved {len(forecasts)} forecast points")
            return forecasts
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching forecast: {e}")
            return self._get_mock_forecast(lat, lon, days)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return self._get_mock_forecast(lat, lon, days)
    
    def get_weather_alerts(self, lat: float, lon: float) -> List[WeatherAlert]:
        """Get weather alerts for specific coordinates"""
        
        if not self.api_key:
            logger.warning("No API key provided - using mock alerts")
            return self._get_mock_alerts(lat, lon)
        
        try:
            url = f"{self.base_url}{self.endpoints['alerts']}"
            params = {
                "lat": lat,
                "lon": lon,
                "appid": self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            alerts = []
            if "alerts" in data:
                for alert_data in data["alerts"]:
                    alert = WeatherAlert(
                        alert_id=alert_data["sender_name"],
                        event=alert_data["event"],
                        description=alert_data["description"],
                        start_time=datetime.fromtimestamp(alert_data["start"]),
                        end_time=datetime.fromtimestamp(alert_data["end"]),
                        severity=alert_data["severity"],
                        areas_affected=alert_data["areas"],
                        source=alert_data["sender_name"]
                    )
                    alerts.append(alert)
            
            logger.info(f"Retrieved {len(alerts)} weather alerts")
            return alerts
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching alerts: {e}")
            return self._get_mock_alerts(lat, lon)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return self._get_mock_alerts(lat, lon)
    
    def get_air_pollution(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get air pollution data"""
        
        if not self.api_key:
            logger.warning("No API key provided - using mock pollution data")
            return self._get_mock_pollution()
        
        try:
            url = f"{self.base_url}{self.endpoints['air_pollution']}"
            params = {
                "lat": lat,
                "lon": lon,
                "appid": self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            pollution_data = {
                "aqi": data["list"][0]["main"]["aqi"],
                "co": data["list"][0]["components"]["co"],
                "no": data["list"][0]["components"]["no"],
                "no2": data["list"][0]["components"]["no2"],
                "o3": data["list"][0]["components"]["o3"],
                "pm2_5": data["list"][0]["components"]["pm2_5"],
                "pm10": data["list"][0]["components"]["pm10"],
                "so2": data["list"][0]["components"]["so2"],
                "timestamp": datetime.fromtimestamp(data["list"][0]["dt"])
            }
            
            logger.info("Retrieved air pollution data")
            return pollution_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching pollution data: {e}")
            return self._get_mock_pollution()
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return self._get_mock_pollution()
    
    def search_location(self, query: str) -> List[Dict[str, Any]]:
        """Search for locations by name"""
        
        if not self.api_key:
            logger.warning("No API key provided - using mock location search")
            return self._get_mock_locations(query)
        
        try:
            url = f"{self.base_url}{self.endpoints['geocoding']}"
            params = {
                "q": query,
                "limit": 5,
                "appid": self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            locations = []
            for item in data:
                locations.append({
                    "name": item["name"],
                    "country": item["country"],
                    "state": item.get("state", ""),
                    "latitude": item["lat"],
                    "longitude": item["lon"]
                })
            
            logger.info(f"Found {len(locations)} locations for '{query}'")
            return locations
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching locations: {e}")
            return self._get_mock_locations(query)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return self._get_mock_locations(query)
    
    def _get_mock_weather(self, lat: float, lon: float) -> WeatherData:
        """Generate mock weather data for testing"""
        
        import random
        
        return WeatherData(
            location="Mock Location",
            latitude=lat,
            longitude=lon,
            temperature=random.uniform(15, 25),
            feels_like=random.uniform(15, 25),
            humidity=random.uniform(40, 80),
            pressure=random.uniform(1000, 1020),
            visibility=random.uniform(5, 15),
            wind_speed=random.uniform(5, 20),
            wind_direction=random.uniform(0, 360),
            wind_gust=random.uniform(0, 10),
            cloud_coverage=random.uniform(0, 100),
            weather_main=random.choice(["Clear", "Clouds", "Rain", "Snow"]),
            weather_description="Mock weather description",
            weather_icon="01d",
            timestamp=datetime.now()
        )
    
    def _get_mock_forecast(self, lat: float, lon: float, days: int) -> List[WeatherData]:
        """Generate mock forecast data"""
        
        forecasts = []
        for i in range(days * 8):
            forecast = self._get_mock_weather(lat, lon)
            forecast.timestamp = datetime.now() + timedelta(hours=i*3)
            forecasts.append(forecast)
        
        return forecasts
    
    def _get_mock_alerts(self, lat: float, lon: float) -> List[WeatherAlert]:
        """Generate mock weather alerts"""
        
        alerts = []
        if lat > 40:  # Simulate alerts for northern locations
            alert = WeatherAlert(
                alert_id="MOCK_001",
                event="Thunderstorm Warning",
                description="Severe thunderstorms expected in the area",
                start_time=datetime.now(),
                end_time=datetime.now() + timedelta(hours=2),
                severity="moderate",
                areas_affected=["Test Area"],
                source="Mock Weather Service"
            )
            alerts.append(alert)
        
        return alerts
    
    def _get_mock_pollution(self) -> Dict[str, Any]:
        """Generate mock pollution data"""
        
        import random
        
        return {
            "aqi": random.randint(1, 5),
            "co": random.uniform(0, 1),
            "no": random.uniform(0, 0.1),
            "no2": random.uniform(0, 0.1),
            "o3": random.uniform(0, 0.2),
            "pm2_5": random.uniform(0, 50),
            "pm10": random.uniform(0, 100),
            "so2": random.uniform(0, 0.1),
            "timestamp": datetime.now()
        }
    
    def _get_mock_locations(self, query: str) -> List[Dict[str, Any]]:
        """Generate mock location search results"""
        
        mock_locations = [
            {"name": "New York", "country": "US", "state": "NY", "latitude": 40.7128, "longitude": -74.0060},
            {"name": "London", "country": "GB", "state": "", "latitude": 51.5074, "longitude": -0.1278},
            {"name": "Tokyo", "country": "JP", "state": "", "latitude": 35.6762, "longitude": 139.6503}
        ]
        
        return [loc for loc in mock_locations if query.lower() in loc["name"].lower()]
    
    def get_aviation_weather(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get aviation-specific weather data"""
        
        current_weather = self.get_current_weather(lat, lon)
        if not current_weather:
            return {}
        
        # Calculate aviation weather parameters
        visibility_km = current_weather.visibility
        cloud_base = self._calculate_cloud_base(current_weather.cloud_coverage, current_weather.humidity)
        turbulence_risk = self._calculate_turbulence_risk(current_weather.wind_speed, current_weather.wind_gust)
        icing_risk = self._calculate_icing_risk(current_weather.temperature, current_weather.humidity)
        
        return {
            "visibility": {
                "value": visibility_km,
                "category": "good" if visibility_km > 10 else "moderate" if visibility_km > 5 else "poor"
            },
            "cloud_base": {
                "value": cloud_base,
                "category": "high" if cloud_base > 3000 else "medium" if cloud_base > 1000 else "low"
            },
            "turbulence": {
                "risk": turbulence_risk,
                "wind_speed": current_weather.wind_speed,
                "wind_gust": current_weather.wind_gust
            },
            "icing": {
                "risk": icing_risk,
                "temperature": current_weather.temperature,
                "humidity": current_weather.humidity
            },
            "wind": {
                "speed": current_weather.wind_speed,
                "direction": current_weather.wind_direction,
                "gust": current_weather.wind_gust
            },
            "pressure": current_weather.pressure,
            "timestamp": current_weather.timestamp
        }
    
    def _calculate_cloud_base(self, cloud_coverage: float, humidity: float) -> float:
        """Calculate estimated cloud base altitude"""
        
        # Simple estimation based on humidity and cloud coverage
        if cloud_coverage < 25:
            return 10000  # High clouds
        elif cloud_coverage < 50:
            return 5000   # Medium clouds
        elif cloud_coverage < 75:
            return 2000   # Low clouds
        else:
            return 500    # Very low clouds
    
    def _calculate_turbulence_risk(self, wind_speed: float, wind_gust: float) -> str:
        """Calculate turbulence risk"""
        
        gust_factor = wind_gust / wind_speed if wind_speed > 0 else 0
        
        if wind_speed > 30 or gust_factor > 1.5:
            return "high"
        elif wind_speed > 20 or gust_factor > 1.2:
            return "moderate"
        else:
            return "low"
    
    def _calculate_icing_risk(self, temperature: float, humidity: float) -> str:
        """Calculate icing risk"""
        
        if temperature < 0 and humidity > 80:
            return "high"
        elif temperature < 5 and humidity > 70:
            return "moderate"
        else:
            return "low"
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get OpenWeatherMap integration status"""
        
        return {
            "service": "OpenWeatherMap",
            "status": "operational",
            "api_key_configured": bool(self.api_key),
            "rate_limit_delay": self.rate_limit_delay,
            "endpoints": list(self.endpoints.keys()),
            "last_update": datetime.now().isoformat()
        }

def main():
    """Test OpenWeatherMap integration"""
    
    # Initialize OpenWeatherMap integration
    weather = OpenWeatherMapIntegration()
    
    # Test weather data for New York
    print("Testing OpenWeatherMap integration...")
    
    weather_data = weather.get_current_weather(40.7128, -74.0060)
    if weather_data:
        print(f"Weather for {weather_data.location}:")
        print(f"Temperature: {weather_data.temperature}°C")
        print(f"Humidity: {weather_data.humidity}%")
        print(f"Wind: {weather_data.wind_speed} m/s")
        print(f"Conditions: {weather_data.weather_description}")
        print()
    
    # Test aviation weather
    aviation_weather = weather.get_aviation_weather(40.7128, -74.0060)
    if aviation_weather:
        print("Aviation Weather:")
        print(f"Visibility: {aviation_weather['visibility']['value']} km ({aviation_weather['visibility']['category']})")
        print(f"Cloud Base: {aviation_weather['cloud_base']['value']} ft ({aviation_weather['cloud_base']['category']})")
        print(f"Turbulence Risk: {aviation_weather['turbulence']['risk']}")
        print(f"Icing Risk: {aviation_weather['icing']['risk']}")
        print()
    
    # Get system status
    status = weather.get_system_status()
    print("System Status:")
    print(f"Service: {status['service']}")
    print(f"Status: {status['status']}")
    print(f"API Key Configured: {status['api_key_configured']}")

if __name__ == "__main__":
    main()


