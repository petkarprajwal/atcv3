"""
Enhanced Weather API Client
Secure API client for weather data with fallback to demo mode
"""

import os
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import random


class EnhancedWeatherAPI:
    """Enhanced Weather API client with secure handling and demo fallback"""
    
    def __init__(self):
        """Initialize the weather API client"""
        # Try to get API key from environment variables
        self.api_key = os.getenv('OPENWEATHERMAP_API_KEY')
        self.base_url = "https://api.openweathermap.org/data/2.5"
        
        # If no API key, we'll use demo mode
        self.demo_mode = not bool(self.api_key)
        
        if self.demo_mode:
            print("Warning: No OpenWeatherMap API key found. Running in demo mode.")
    
    def get_current_weather(self, lat: float, lon: float, use_demo_fallback: bool = True) -> Optional[Dict[str, Any]]:
        """
        Get current weather for coordinates
        
        Args:
            lat: Latitude
            lon: Longitude
            use_demo_fallback: Whether to use demo data on API failure
            
        Returns:
            Weather data dictionary or None
        """
        if self.demo_mode or not self.api_key:
            if use_demo_fallback:
                return self._generate_demo_weather(lat, lon)
            return None
        
        try:
            # Build API request
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'metric'
            }
            
            response = requests.get(
                f"{self.base_url}/weather",
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return self._normalize_weather_data(data)
            else:
                print(f"Weather API error: {response.status_code}")
                if use_demo_fallback:
                    return self._generate_demo_weather(lat, lon)
                return None
                
        except Exception as e:
            print(f"Weather API request failed: {e}")
            if use_demo_fallback:
                return self._generate_demo_weather(lat, lon)
            return None
    
    def get_forecast(self, lat: float, lon: float, days: int = 3, use_demo_fallback: bool = True) -> Optional[Dict[str, Any]]:
        """
        Get weather forecast for coordinates
        
        Args:
            lat: Latitude
            lon: Longitude
            days: Number of forecast days
            use_demo_fallback: Whether to use demo data on API failure
            
        Returns:
            Forecast data dictionary or None
        """
        if self.demo_mode or not self.api_key:
            if use_demo_fallback:
                return self._generate_demo_forecast(lat, lon, days)
            return None
        
        try:
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'metric',
                'cnt': days * 8  # 8 forecasts per day (3-hour intervals)
            }
            
            response = requests.get(
                f"{self.base_url}/forecast",
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return self._normalize_forecast_data(data)
            else:
                print(f"Forecast API error: {response.status_code}")
                if use_demo_fallback:
                    return self._generate_demo_forecast(lat, lon, days)
                return None
                
        except Exception as e:
            print(f"Forecast API request failed: {e}")
            if use_demo_fallback:
                return self._generate_demo_forecast(lat, lon, days)
            return None
    
    def _normalize_weather_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize OpenWeatherMap data to our format
        
        Args:
            data: Raw API response data
            
        Returns:
            Normalized weather data
        """
        try:
            return {
                'temp_c': data['main']['temp'],
                'humidity': data['main']['humidity'],
                'pressure_mb': data['main']['pressure'],
                'wind_kph': data.get('wind', {}).get('speed', 0) * 3.6,  # Convert m/s to kph
                'wind_dir': data.get('wind', {}).get('deg', 0),
                'vis_km': data.get('visibility', 10000) / 1000,  # Convert meters to km
                'condition': data['weather'][0]['description'] if data.get('weather') else 'Unknown',
                'last_updated': datetime.now().isoformat(),
                'is_demo': False
            }
        except KeyError as e:
            print(f"Error normalizing weather data: {e}")
            return self._generate_demo_weather(0, 0)
    
    def _normalize_forecast_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize forecast data to our format
        
        Args:
            data: Raw forecast API response
            
        Returns:
            Normalized forecast data
        """
        try:
            forecast_list = []
            
            for item in data.get('list', []):
                forecast_list.append({
                    'datetime': item['dt_txt'],
                    'temp_c': item['main']['temp'],
                    'humidity': item['main']['humidity'],
                    'pressure_mb': item['main']['pressure'],
                    'wind_kph': item.get('wind', {}).get('speed', 0) * 3.6,
                    'condition': item['weather'][0]['description'],
                    'precipitation': item.get('rain', {}).get('3h', 0)
                })
            
            return {
                'location': data.get('city', {}).get('name', 'Unknown'),
                'forecast': forecast_list,
                'is_demo': False
            }
            
        except KeyError as e:
            print(f"Error normalizing forecast data: {e}")
            return self._generate_demo_forecast(0, 0, 3)
    
    def _generate_demo_weather(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Generate realistic demo weather data
        
        Args:
            lat: Latitude (used for realistic temperature)
            lon: Longitude
            
        Returns:
            Demo weather data
        """
        # Base temperature on latitude (rough approximation)
        base_temp = 25 - abs(lat) * 0.3
        
        return {
            'temp_c': round(base_temp + random.uniform(-5, 5), 1),
            'humidity': random.randint(30, 90),
            'pressure_mb': round(random.uniform(990, 1025), 1),
            'wind_kph': round(random.uniform(0, 25), 1),
            'wind_dir': random.randint(0, 360),
            'vis_km': round(random.uniform(2, 15), 1),
            'condition': random.choice([
                'Clear', 'Partly cloudy', 'Cloudy', 'Light rain', 
                'Rain', 'Thunderstorm', 'Fog', 'Mist'
            ]),
            'last_updated': datetime.now().isoformat(),
            'is_demo': True
        }
    
    def _generate_demo_forecast(self, lat: float, lon: float, days: int) -> Dict[str, Any]:
        """
        Generate demo forecast data
        
        Args:
            lat: Latitude
            lon: Longitude
            days: Number of forecast days
            
        Returns:
            Demo forecast data
        """
        forecast_list = []
        base_temp = 25 - abs(lat) * 0.3
        
        for day in range(days):
            for hour in range(0, 24, 3):  # Every 3 hours
                forecast_time = datetime.now() + timedelta(days=day, hours=hour)
                
                # Temperature variation throughout the day
                hour_temp_variation = 5 * (1 - abs(hour - 12) / 12)  # Peak at noon
                
                forecast_list.append({
                    'datetime': forecast_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'temp_c': round(base_temp + hour_temp_variation + random.uniform(-3, 3), 1),
                    'humidity': random.randint(30, 90),
                    'pressure_mb': round(random.uniform(990, 1025), 1),
                    'wind_kph': round(random.uniform(5, 20), 1),
                    'condition': random.choice([
                        'Clear', 'Partly cloudy', 'Cloudy', 'Light rain', 'Rain'
                    ]),
                    'precipitation': round(random.uniform(0, 2), 1) if random.random() < 0.3 else 0
                })
        
        return {
            'location': f'Location {lat:.2f},{lon:.2f}',
            'forecast': forecast_list,
            'is_demo': True
        }
    
    def get_air_quality(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """
        Get air quality data for coordinates
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Air quality data or demo data
        """
        if self.demo_mode or not self.api_key:
            return self._generate_demo_air_quality()
        
        try:
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key
            }
            
            response = requests.get(
                f"{self.base_url}/air_pollution",
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return self._normalize_air_quality_data(data)
            else:
                return self._generate_demo_air_quality()
                
        except Exception as e:
            print(f"Air quality API request failed: {e}")
            return self._generate_demo_air_quality()
    
    def _normalize_air_quality_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize air quality data"""
        try:
            aqi_data = data['list'][0]
            return {
                'aqi': aqi_data['main']['aqi'],
                'co': aqi_data['components']['co'],
                'no2': aqi_data['components']['no2'],
                'o3': aqi_data['components']['o3'],
                'pm2_5': aqi_data['components']['pm2_5'],
                'pm10': aqi_data['components']['pm10'],
                'is_demo': False
            }
        except KeyError:
            return self._generate_demo_air_quality()
    
    def _generate_demo_air_quality(self) -> Dict[str, Any]:
        """Generate demo air quality data"""
        return {
            'aqi': random.randint(1, 5),
            'co': round(random.uniform(200, 400), 2),
            'no2': round(random.uniform(10, 50), 2),
            'o3': round(random.uniform(50, 150), 2),
            'pm2_5': round(random.uniform(5, 25), 2),
            'pm10': round(random.uniform(10, 50), 2),
            'is_demo': True
        }


# Global instance for easy import
weather_api = EnhancedWeatherAPI()