#!/usr/bin/env python3
"""
Unified API Manager
Centralized management of all real-time APIs
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
import logging
from dataclasses import dataclass, asdict
import threading
from queue import Queue

# Import our API integrations
from .opensky_integration import OpenSkyIntegration, FlightData
from .openweathermap_integration import OpenWeatherMapIntegration, WeatherData
from .faa_integration import FAAIntegration, AirportStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class APIConfig:
    """API configuration"""
    service_name: str
    enabled: bool
    api_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    rate_limit_delay: float = 1.0
    max_retries: int = 3
    timeout: int = 10

@dataclass
class SystemStatus:
    """Overall system status"""
    timestamp: datetime
    total_apis: int
    active_apis: int
    failed_apis: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    data_points_collected: int
    system_health: str

class UnifiedAPIManager:
    """Unified API management system"""
    
    def __init__(self):
        # API configurations
        self.api_configs = {
            "opensky": APIConfig(
                service_name="OpenSky Network",
                enabled=True,
                rate_limit_delay=6.0,  # 10 requests per minute
                max_retries=3
            ),
            "openweathermap": APIConfig(
                service_name="OpenWeatherMap",
                enabled=True,
                rate_limit_delay=1.0,  # 60 requests per minute
                max_retries=3
            ),
            "faa": APIConfig(
                service_name="FAA Airport Status",
                enabled=True,
                rate_limit_delay=1.0,
                max_retries=3
            )
        }
        
        # Initialize API integrations
        self.apis = {
            "opensky": None,
            "openweathermap": None,
            "faa": None
        }
        
        # Data storage
        self.flight_data: List[FlightData] = []
        self.weather_data: Dict[str, WeatherData] = {}
        self.airport_status: Dict[str, AirportStatus] = {}
        
        # Performance metrics
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "data_points_collected": 0,
            "last_update": datetime.now()
        }
        
        # Data update callbacks
        self.update_callbacks: List[Callable] = []
        
        # Background update thread
        self.update_thread = None
        self.running = False
        
        logger.info("Unified API Manager initialized")
    
    def configure_api(self, api_name: str, config: APIConfig):
        """Configure specific API"""
        
        if api_name in self.api_configs:
            self.api_configs[api_name] = config
            logger.info(f"Configured {api_name} API")
        else:
            logger.warning(f"Unknown API: {api_name}")
    
    def initialize_apis(self):
        """Initialize all enabled APIs"""
        
        # Initialize OpenSky
        if self.api_configs["opensky"].enabled:
            config = self.api_configs["opensky"]
            self.apis["opensky"] = OpenSkyIntegration(
                username=config.username,
                password=config.password
            )
            logger.info("OpenSky API initialized")
        
        # Initialize OpenWeatherMap
        if self.api_configs["openweathermap"].enabled:
            config = self.api_configs["openweathermap"]
            self.apis["openweathermap"] = OpenWeatherMapIntegration(
                api_key=config.api_key
            )
            logger.info("OpenWeatherMap API initialized")
        
        # Initialize FAA
        if self.api_configs["faa"].enabled:
            self.apis["faa"] = FAAIntegration()
            logger.info("FAA API initialized")
    
    def start_background_updates(self, update_interval: int = 60):
        """Start background data updates"""
        
        if self.update_thread and self.update_thread.is_alive():
            logger.warning("Background updates already running")
            return
        
        self.running = True
        self.update_thread = threading.Thread(
            target=self._background_update_loop,
            args=(update_interval,),
            daemon=True
        )
        self.update_thread.start()
        logger.info(f"Started background updates every {update_interval} seconds")
    
    def stop_background_updates(self):
        """Stop background data updates"""
        
        self.running = False
        if self.update_thread:
            self.update_thread.join(timeout=5)
        logger.info("Stopped background updates")
    
    def _background_update_loop(self, update_interval: int):
        """Background update loop"""
        
        while self.running:
            try:
                self.update_all_data()
                time.sleep(update_interval)
            except Exception as e:
                logger.error(f"Error in background update: {e}")
                time.sleep(update_interval)
    
    def update_all_data(self):
        """Update all data from all APIs"""
        
        logger.info("Updating all data...")
        
        # Update flight data
        if self.apis["opensky"]:
            self._update_flight_data()
        
        # Update weather data
        if self.apis["openweathermap"]:
            self._update_weather_data()
        
        # Update airport status
        if self.apis["faa"]:
            self._update_airport_status()
        
        # Notify callbacks
        self._notify_callbacks()
        
        logger.info("Data update completed")
    
    def _update_flight_data(self):
        """Update flight data from OpenSky"""
        
        try:
            config = self.api_configs["opensky"]
            time.sleep(config.rate_limit_delay)
            
            # Get flights in major US airspace
            flights = self.apis["opensky"].get_flights_by_area(
                min_lat=25.0, max_lat=49.0,
                min_lon=-125.0, max_lon=-66.0
            )
            
            self.flight_data = flights
            self.metrics["successful_requests"] += 1
            self.metrics["data_points_collected"] += len(flights)
            
            logger.info(f"Updated {len(flights)} flight records")
            
        except Exception as e:
            logger.error(f"Error updating flight data: {e}")
            self.metrics["failed_requests"] += 1
    
    def _update_weather_data(self):
        """Update weather data from OpenWeatherMap"""
        
        try:
            config = self.api_configs["openweathermap"]
            time.sleep(config.rate_limit_delay)
            
            # Major US cities for weather data
            cities = [
                (40.7128, -74.0060, "New York"),
                (34.0522, -118.2437, "Los Angeles"),
                (41.8781, -87.6298, "Chicago"),
                (32.7767, -96.7970, "Dallas"),
                (33.7490, -84.3880, "Atlanta")
            ]
            
            for lat, lon, city in cities:
                weather = self.apis["openweathermap"].get_current_weather(lat, lon)
                if weather:
                    self.weather_data[city] = weather
            
            self.metrics["successful_requests"] += 1
            self.metrics["data_points_collected"] += len(self.weather_data)
            
            logger.info(f"Updated weather for {len(self.weather_data)} cities")
            
        except Exception as e:
            logger.error(f"Error updating weather data: {e}")
            self.metrics["failed_requests"] += 1
    
    def _update_airport_status(self):
        """Update airport status from FAA"""
        
        try:
            config = self.api_configs["faa"]
            time.sleep(config.rate_limit_delay)
            
            # Major US airports
            airports = ["JFK", "LAX", "ORD", "DFW", "ATL", "DEN", "SFO", "SEA"]
            
            for airport in airports:
                status = self.apis["faa"].get_airport_status(airport)
                if status:
                    self.airport_status[airport] = status
            
            self.metrics["successful_requests"] += 1
            self.metrics["data_points_collected"] += len(self.airport_status)
            
            logger.info(f"Updated status for {len(self.airport_status)} airports")
            
        except Exception as e:
            logger.error(f"Error updating airport status: {e}")
            self.metrics["failed_requests"] += 1
    
    def get_flights_in_area(self, min_lat: float, max_lat: float, 
                           min_lon: float, max_lon: float) -> List[FlightData]:
        """Get flights in specific area"""
        
        if not self.apis["opensky"]:
            return []
        
        try:
            config = self.api_configs["opensky"]
            time.sleep(config.rate_limit_delay)
            
            flights = self.apis["opensky"].get_flights_by_area(min_lat, max_lat, min_lon, max_lon)
            self.metrics["successful_requests"] += 1
            
            return flights
            
        except Exception as e:
            logger.error(f"Error getting flights in area: {e}")
            self.metrics["failed_requests"] += 1
            return []
    
    def get_weather_at_location(self, lat: float, lon: float) -> Optional[WeatherData]:
        """Get weather at specific location"""
        
        if not self.apis["openweathermap"]:
            return None
        
        try:
            config = self.api_configs["openweathermap"]
            time.sleep(config.rate_limit_delay)
            
            weather = self.apis["openweathermap"].get_current_weather(lat, lon)
            self.metrics["successful_requests"] += 1
            
            return weather
            
        except Exception as e:
            logger.error(f"Error getting weather: {e}")
            self.metrics["failed_requests"] += 1
            return None
    
    def get_airport_status(self, airport_code: str) -> Optional[AirportStatus]:
        """Get status for specific airport"""
        
        if not self.apis["faa"]:
            return None
        
        try:
            config = self.api_configs["faa"]
            time.sleep(config.rate_limit_delay)
            
            status = self.apis["faa"].get_airport_status(airport_code)
            self.metrics["successful_requests"] += 1
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting airport status: {e}")
            self.metrics["failed_requests"] += 1
            return None
    
    def get_aviation_weather(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get aviation-specific weather data"""
        
        if not self.apis["openweathermap"]:
            return {}
        
        try:
            config = self.api_configs["openweathermap"]
            time.sleep(config.rate_limit_delay)
            
            aviation_weather = self.apis["openweathermap"].get_aviation_weather(lat, lon)
            self.metrics["successful_requests"] += 1
            
            return aviation_weather
            
        except Exception as e:
            logger.error(f"Error getting aviation weather: {e}")
            self.metrics["failed_requests"] += 1
            return {}
    
    def get_system_overview(self) -> Dict[str, Any]:
        """Get comprehensive system overview"""
        
        overview = {
            "timestamp": datetime.now(),
            "apis": {},
            "data_summary": {
                "total_flights": len(self.flight_data),
                "weather_locations": len(self.weather_data),
                "airports_tracked": len(self.airport_status)
            },
            "metrics": self.metrics.copy()
        }
        
        # Get individual API status
        for api_name, api in self.apis.items():
            if api:
                overview["apis"][api_name] = api.get_system_status()
            else:
                overview["apis"][api_name] = {"status": "not_initialized"}
        
        return overview
    
    def get_system_health(self) -> SystemStatus:
        """Get overall system health"""
        
        total_apis = len(self.apis)
        active_apis = sum(1 for api in self.apis.values() if api is not None)
        failed_apis = total_apis - active_apis
        
        total_requests = self.metrics["total_requests"]
        successful_requests = self.metrics["successful_requests"]
        failed_requests = self.metrics["failed_requests"]
        
        # Calculate health score
        if total_requests == 0:
            health_score = "unknown"
        else:
            success_rate = successful_requests / total_requests
            if success_rate >= 0.9:
                health_score = "excellent"
            elif success_rate >= 0.7:
                health_score = "good"
            elif success_rate >= 0.5:
                health_score = "fair"
            else:
                health_score = "poor"
        
        return SystemStatus(
            timestamp=datetime.now(),
            total_apis=total_apis,
            active_apis=active_apis,
            failed_apis=failed_apis,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            data_points_collected=self.metrics["data_points_collected"],
            system_health=health_score
        )
    
    def add_update_callback(self, callback: Callable):
        """Add callback for data updates"""
        
        self.update_callbacks.append(callback)
        logger.info("Added update callback")
    
    def remove_update_callback(self, callback: Callable):
        """Remove update callback"""
        
        if callback in self.update_callbacks:
            self.update_callbacks.remove(callback)
            logger.info("Removed update callback")
    
    def _notify_callbacks(self):
        """Notify all callbacks of data update"""
        
        for callback in self.update_callbacks:
            try:
                callback(self.get_system_overview())
            except Exception as e:
                logger.error(f"Error in callback: {e}")
    
    def export_data(self, format: str = "json") -> str:
        """Export all data"""
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "flight_data": [asdict(flight) for flight in self.flight_data],
            "weather_data": {city: asdict(weather) for city, weather in self.weather_data.items()},
            "airport_status": {code: asdict(status) for code, status in self.airport_status.items()},
            "metrics": self.metrics
        }
        
        if format == "json":
            return json.dumps(data, indent=2, default=str)
        else:
            return str(data)
    
    def reset_metrics(self):
        """Reset performance metrics"""
        
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "data_points_collected": 0,
            "last_update": datetime.now()
        }
        logger.info("Performance metrics reset")

def main():
    """Test unified API manager"""
    
    # Initialize API manager
    manager = UnifiedAPIManager()
    
    # Configure APIs (you can add your API keys here)
    manager.configure_api("opensky", APIConfig(
        service_name="OpenSky Network",
        enabled=True,
        username=None,  # Add your OpenSky username
        password=None  # Add your OpenSky password
    ))
    
    manager.configure_api("openweathermap", APIConfig(
        service_name="OpenWeatherMap",
        enabled=True,
        api_key=None  # Add your OpenWeatherMap API key
    ))
    
    # Initialize APIs
    manager.initialize_apis()
    
    # Test individual API calls
    print("Testing Unified API Manager...")
    
    # Test flight data
    flights = manager.get_flights_in_area(40.0, 41.0, -75.0, -73.0)
    print(f"Found {len(flights)} flights in New York area")
    
    # Test weather data
    weather = manager.get_weather_at_location(40.7128, -74.0060)
    if weather:
        print(f"Weather in {weather.location}: {weather.temperature}°C, {weather.weather_description}")
    
    # Test airport status
    airport_status = manager.get_airport_status("JFK")
    if airport_status:
        print(f"JFK Status: {airport_status.delay_status} ({airport_status.delay_minutes} min delay)")
    
    # Get system overview
    overview = manager.get_system_overview()
    print(f"\nSystem Overview:")
    print(f"Total Flights: {overview['data_summary']['total_flights']}")
    print(f"Weather Locations: {overview['data_summary']['weather_locations']}")
    print(f"Airports Tracked: {overview['data_summary']['airports_tracked']}")
    
    # Get system health
    health = manager.get_system_health()
    print(f"System Health: {health.system_health}")
    print(f"Active APIs: {health.active_apis}/{health.total_apis}")

if __name__ == "__main__":
    main()


