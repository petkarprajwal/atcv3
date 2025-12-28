"""
Weather API Manager for Enhanced Weather System
Supports OpenWeatherMap with secure API client and fallback to demo mode
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional

from utils.enhanced_weather_api import EnhancedWeatherAPI

class WeatherData:
    def __init__(self, station_id, timestamp, temperature, humidity, pressure, wind_speed, wind_direction, visibility, conditions, precipitation, cloud_cover, source):
        self.station_id = station_id
        self.timestamp = timestamp
        self.temperature = temperature
        self.humidity = humidity
        self.pressure = pressure
        self.wind_speed = wind_speed
        self.wind_direction = wind_direction
        self.visibility = visibility
        self.conditions = conditions
        self.precipitation = precipitation
        self.cloud_cover = cloud_cover
        self.source = source
        
    def to_dict(self):
        return self.__dict__


class EnhancedWeatherManager:
    """Weather Manager that uses secure API client with proper error handling and fallbacks"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize weather manager
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.primary_source = config.get('primary_source', 'openweathermap')
        self.use_demo_fallback = config.get('use_demo_fallback', True)
        self.weather_api = EnhancedWeatherAPI()
        
        # For location name to coordinates mapping
        self.location_cache = {}
    
    async def __aenter__(self):
        # No external session to initialize; return self for compatibility
        return self
    
    async def __aexit__(self, exc_type, exc, tb):
        # Nothing to cleanup; maintain async context manager interface
        return False
        
    async def get_weather(self, station_id: str) -> WeatherData:
        """
        Get weather data for a station/location
        
        Args:
            station_id: Location name or ID
            
        Returns:
            WeatherData object
        """
        # Check if we have coordinates for this station in cache
        if station_id in self.location_cache:
            lat, lon = self.location_cache[station_id]
        else:
            # For simplicity, we'll use some default coordinates if not found
            # In production, this would use a geocoding service
            lat, lon = self._get_default_coordinates(station_id)
            self.location_cache[station_id] = (lat, lon)
            
        # Get weather data using our secure client
        weather_data = self.weather_api.get_current_weather(
            lat=lat, 
            lon=lon,
            use_demo_fallback=self.use_demo_fallback
        )
        
        if weather_data:
            # Convert to WeatherData object
            return WeatherData(
                station_id=station_id,
                timestamp=datetime.fromisoformat(weather_data.get('last_updated', datetime.now().isoformat())),
                temperature=weather_data.get('temp_c', 20.0),
                humidity=weather_data.get('humidity', 50),
                pressure=weather_data.get('pressure_mb', 1013.0),
                wind_speed=weather_data.get('wind_kph', 5.0) / 3.6,  # Convert to m/s
                wind_direction=weather_data.get('wind_dir', 0),
                visibility=weather_data.get('vis_km', 10.0),
                conditions=weather_data.get('condition', 'Unknown'),
                precipitation=0.0,  # Not directly available in our format
                cloud_cover=0,  # Not directly available in our format
                source='openweathermap' if not weather_data.get('is_demo', False) else 'demo'
            )
        else:
            # If all else fails, generate demo data
            return self._generate_fallback_weather(station_id)
    
    async def get_batch_weather(self, stations: List[str]) -> Dict[str, WeatherData]:
        """
        Get weather data for multiple stations
        
        Args:
            stations: List of station IDs/names
            
        Returns:
            Dictionary of station_id -> WeatherData
        """
        results = {}
        
        # Process all weather requests concurrently for better performance
        tasks = [self.get_weather(station) for station in stations]
        weather_data_list = await asyncio.gather(*tasks)
        
        # Map results to dictionary
        for station, weather in zip(stations, weather_data_list):
            results[station] = weather
            
        return results
    
    def _get_default_coordinates(self, location_name: str) -> tuple:
        """
        Get default coordinates for common airports/locations
        
        Args:
            location_name: Location name
            
        Returns:
            Tuple of (latitude, longitude)
        """
        # Map of common airport codes to coordinates
        airport_coords = {
            'JFK': (40.6413, -73.7781),
            'LAX': (33.9416, -118.4085),
            'ORD': (41.9742, -87.9073),
            'LHR': (51.4700, -0.4543),
            'CDG': (49.0097, 2.5479),
            'HND': (35.5494, 139.7798),
            'SIN': (1.3644, 103.9915),
            # Add more common airports as needed
        }
        
        # Try to match by airport code
        if location_name.upper() in airport_coords:
            return airport_coords[location_name.upper()]
        
        # Default to a random location based on the name hash
        # This is a simple way to make consistent coordinates for unknown locations
        import hashlib
        hash_val = int(hashlib.md5(location_name.encode()).hexdigest(), 16)
        lat = (hash_val % 180) - 90
        lon = (hash_val // 180 % 360) - 180
        
        return (lat, lon)
    
    def _generate_fallback_weather(self, station_id: str) -> WeatherData:
        """
        Generate fallback weather data if all API requests fail
        
        Args:
            station_id: Location name/ID
            
        Returns:
            WeatherData with demo values
        """
        import random
        
        return WeatherData(
            station_id=station_id,
            timestamp=datetime.now(),
            temperature=random.uniform(15, 30),
            humidity=random.uniform(40, 80),
            pressure=random.uniform(990, 1025),
            wind_speed=random.uniform(0, 20),
            wind_direction=random.uniform(0, 360),
            visibility=random.uniform(2, 10),
            conditions=random.choice(['clear', 'cloudy', 'rain', 'storm']),
            precipitation=random.uniform(0, 10),
            cloud_cover=random.uniform(0, 100),
            source='demo'
        )

    async def get_forecast(self, station_id: str, days: int = 3) -> Dict[str, Any]:
        """
        Get weather forecast for a location
        
        Args:
            station_id: Location name/ID
            days: Number of forecast days
            
        Returns:
            Dictionary with forecast data
        """
        # Check if we have coordinates for this station in cache
        if station_id in self.location_cache:
            lat, lon = self.location_cache[station_id]
        else:
            lat, lon = self._get_default_coordinates(station_id)
            self.location_cache[station_id] = (lat, lon)
        
        # Get forecast using enhanced API
        return self.weather_api.get_forecast(lat, lon, days, use_demo_fallback=self.use_demo_fallback)