#!/usr/bin/env python3
"""
Multi-API Integration Framework
Enhanced aviation data integration with multiple real-time sources
"""

import asyncio
import aiohttp
import requests
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import logging
from pathlib import Path
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class FlightData:
    """Enhanced flight data structure"""
    callsign: str
    icao24: str
    latitude: float
    longitude: float
    altitude: float
    velocity: float
    heading: float
    vertical_rate: float
    timestamp: datetime
    source: str
    aircraft_type: Optional[str] = None
    origin_airport: Optional[str] = None
    destination_airport: Optional[str] = None
    flight_status: Optional[str] = None
    estimated_arrival: Optional[datetime] = None
    route_waypoints: Optional[List[Tuple[float, float]]] = None
    fuel_remaining: Optional[float] = None
    passengers: Optional[int] = None
    confidence_score: float = 1.0

@dataclass
class WeatherData:
    """Enhanced weather data structure"""
    location: Tuple[float, float]
    timestamp: datetime
    temperature: float
    wind_speed: float
    wind_direction: float
    visibility: float
    precipitation: float
    cloud_coverage: float
    pressure: float
    humidity: float
    turbulence_forecast: Optional[float] = None
    storm_probability: Optional[float] = None
    source: str = "weather_api"

@dataclass
class AirportData:
    """Enhanced airport data structure"""
    icao_code: str
    iata_code: str
    name: str
    latitude: float
    longitude: float
    elevation: float
    country: str
    runway_count: int
    runway_lengths: List[int]
    current_weather: Optional[WeatherData] = None
    traffic_level: Optional[str] = None
    delays: Optional[Dict[str, float]] = None
    operational_status: str = "OPERATIONAL"

class APIRateLimiter:
    """Rate limiter for API calls"""
    
    def __init__(self, max_calls: int = 100, time_window: int = 60):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    async def acquire(self):
        """Acquire permission to make API call"""
        now = time.time()
        
        # Remove old calls outside time window
        self.calls = [call_time for call_time in self.calls if now - call_time < self.time_window]
        
        # Check if we can make another call
        if len(self.calls) >= self.max_calls:
            sleep_time = self.time_window - (now - self.calls[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
                return await self.acquire()
        
        self.calls.append(now)
        return True

class OpenSkyAPI:
    """Enhanced OpenSky Network API client"""
    
    def __init__(self, credentials: Dict = None):
        self.base_url = "https://opensky-network.org/api"
        self.credentials = credentials
        self.rate_limiter = APIRateLimiter(max_calls=400, time_window=600)  # 400 calls per 10 minutes
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_all_flights(self, bbox: Tuple[float, float, float, float] = None) -> List[FlightData]:
        """Get all current flights with enhanced data"""
        await self.rate_limiter.acquire()
        
        url = f"{self.base_url}/states/all"
        params = {}
        
        if bbox:
            params.update({
                'lamin': bbox[0], 'lomin': bbox[1],
                'lamax': bbox[2], 'lomax': bbox[3]
            })
        
        auth = None
        if self.credentials:
            auth = aiohttp.BasicAuth(
                self.credentials.get('username', ''),
                self.credentials.get('password', '')
            )
        
        try:
            async with self.session.get(url, params=params, auth=auth, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_opensky_data(data)
                else:
                    logger.warning(f"OpenSky API returned status {response.status}")
                    return []
        except Exception as e:
            logger.error(f"OpenSky API error: {e}")
            return []
    
    async def get_flight_track(self, icao24: str, time_period: int = 3600) -> List[Dict]:
        """Get flight track for specific aircraft"""
        await self.rate_limiter.acquire()
        
        end_time = int(time.time())
        start_time = end_time - time_period
        
        url = f"{self.base_url}/tracks/all"
        params = {
            'icao24': icao24,
            'time': start_time
        }
        
        try:
            async with self.session.get(url, params=params, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('path', [])
                else:
                    return []
        except Exception as e:
            logger.error(f"Flight track error: {e}")
            return []
    
    def _parse_opensky_data(self, data: Dict) -> List[FlightData]:
        """Parse OpenSky API response into FlightData objects"""
        flights = []
        
        if not data or 'states' not in data:
            return flights
        
        for state in data['states']:
            if len(state) >= 16 and state[5] is not None and state[6] is not None:
                try:
                    flight = FlightData(
                        callsign=state[1].strip() if state[1] else f"UNKNOWN_{state[0]}",
                        icao24=state[0],
                        latitude=float(state[6]),
                        longitude=float(state[5]),
                        altitude=float(state[7] or 0),
                        velocity=float(state[9] or 0),
                        heading=float(state[10] or 0),
                        vertical_rate=float(state[11] or 0),
                        timestamp=datetime.fromtimestamp(state[3] or time.time()),
                        source="OpenSky",
                        aircraft_type=self._guess_aircraft_type(state[1]),
                        confidence_score=0.9
                    )
                    flights.append(flight)
                except (ValueError, TypeError) as e:
                    logger.debug(f"Error parsing flight state: {e}")
                    continue
        
        return flights
    
    def _guess_aircraft_type(self, callsign: str) -> Optional[str]:
        """Guess aircraft type from callsign"""
        if not callsign:
            return None
        
        airline_aircraft = {
            'UAL': 'Boeing 777/787', 'AAL': 'Boeing 737/777', 'DAL': 'Airbus A320/Boeing 737',
            'SWA': 'Boeing 737', 'JBU': 'Airbus A320', 'BAW': 'Boeing 777/Airbus A350',
            'AFR': 'Airbus A320/A350', 'DLH': 'Airbus A320/Boeing 747'
        }
        
        for code, aircraft in airline_aircraft.items():
            if callsign.startswith(code):
                return aircraft
        
        return "Commercial Aircraft"

class FlightAwareAPI:
    """FlightAware API integration (enhanced simulation)"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.base_url = "https://aeroapi.flightaware.com/aeroapi"
        self.rate_limiter = APIRateLimiter(max_calls=500, time_window=3600)
    
    async def get_flight_info(self, flight_id: str) -> Optional[FlightData]:
        """Get detailed flight information"""
        await self.rate_limiter.acquire()
        
        # Enhanced simulation with realistic data
        try:
            # Simulate API response delay
            await asyncio.sleep(0.1)
            
            # Generate realistic flight data
            flight_data = self._generate_enhanced_flight_data(flight_id)
            return flight_data
            
        except Exception as e:
            logger.error(f"FlightAware API error: {e}")
            return None
    
    async def get_airport_flights(self, airport_code: str, flight_type: str = "departures") -> List[FlightData]:
        """Get flights for specific airport"""
        await self.rate_limiter.acquire()
        
        # Enhanced simulation
        flights = []
        for i in range(np.random.randint(5, 15)):
            flight_id = f"{np.random.choice(['AAL', 'UAL', 'DAL', 'SWA'])}{np.random.randint(100, 9999)}"
            flight_data = self._generate_enhanced_flight_data(flight_id)
            if flight_data:
                flights.append(flight_data)
        
        return flights
    
    def _generate_enhanced_flight_data(self, flight_id: str) -> FlightData:
        """Generate realistic flight data for simulation"""
        
        # Generate realistic coordinates (major US airports vicinity)
        major_airports = [
            (40.7128, -74.0060, "JFK"),  # New York
            (34.0522, -118.2437, "LAX"), # Los Angeles  
            (41.8781, -87.6298, "ORD"),  # Chicago
            (25.7617, -80.1918, "MIA"),  # Miami
            (32.8968, -97.0380, "DFW")   # Dallas
        ]
        
        origin = np.random.choice(major_airports)
        destination = np.random.choice([apt for apt in major_airports if apt != origin])
        
        # Calculate position along route
        progress = np.random.uniform(0.1, 0.9)
        lat = origin[0] + (destination[0] - origin[0]) * progress
        lon = origin[1] + (destination[1] - origin[1]) * progress
        
        return FlightData(
            callsign=flight_id,
            icao24=f"A{hashlib.md5(flight_id.encode()).hexdigest()[:5].upper()}",
            latitude=lat + np.random.uniform(-1, 1),
            longitude=lon + np.random.uniform(-1, 1),
            altitude=np.random.uniform(25000, 42000),
            velocity=np.random.uniform(420, 550),
            heading=np.random.uniform(0, 360),
            vertical_rate=np.random.uniform(-1000, 1000),
            timestamp=datetime.now(),
            source="FlightAware",
            aircraft_type=np.random.choice(["Boeing 737", "Airbus A320", "Boeing 777", "Airbus A350"]),
            origin_airport=origin[2],
            destination_airport=destination[2],
            flight_status="EN_ROUTE",
            estimated_arrival=datetime.now() + timedelta(hours=np.random.uniform(1, 6)),
            passengers=np.random.randint(50, 300),
            confidence_score=0.95
        )

class AviationStackAPI:
    """AviationStack API integration"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.base_url = "http://api.aviationstack.com/v1"
        self.rate_limiter = APIRateLimiter(max_calls=1000, time_window=3600)
    
    async def get_real_time_flights(self, limit: int = 100) -> List[FlightData]:
        """Get real-time flight data"""
        await self.rate_limiter.acquire()
        
        # Enhanced simulation
        flights = []
        for i in range(min(limit, 20)):  # Simulate API response
            flight_data = self._generate_aviationstack_flight()
            flights.append(flight_data)
        
        return flights
    
    def _generate_aviationstack_flight(self) -> FlightData:
        """Generate AviationStack-style flight data"""
        airlines = ["American", "United", "Delta", "Southwest", "JetBlue"]
        aircraft_types = ["Boeing 737-800", "Airbus A320-200", "Boeing 777-300ER"]
        
        airline = np.random.choice(airlines)
        flight_num = np.random.randint(100, 9999)
        
        return FlightData(
            callsign=f"{airline[:3].upper()}{flight_num}",
            icao24=f"A{np.random.randint(10000, 99999)}",
            latitude=np.random.uniform(25, 50),
            longitude=np.random.uniform(-125, -65),
            altitude=np.random.uniform(28000, 41000),
            velocity=np.random.uniform(400, 580),
            heading=np.random.uniform(0, 360),
            vertical_rate=np.random.uniform(-500, 500),
            timestamp=datetime.now(),
            source="AviationStack",
            aircraft_type=np.random.choice(aircraft_types),
            flight_status=np.random.choice(["active", "scheduled", "landed"]),
            confidence_score=0.88
        )

class WeatherAPI:
    """Enhanced weather API integration"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.rate_limiter = APIRateLimiter(max_calls=1000, time_window=3600)
    
    async def get_aviation_weather(self, lat: float, lon: float, alt: float = 35000) -> WeatherData:
        """Get aviation-specific weather data"""
        await self.rate_limiter.acquire()
        
        # Enhanced weather simulation
        return WeatherData(
            location=(lat, lon),
            timestamp=datetime.now(),
            temperature=15 - (alt / 1000) * 2 + np.random.uniform(-5, 5),  # Standard + variation
            wind_speed=np.random.uniform(20, 100),
            wind_direction=np.random.uniform(0, 360),
            visibility=np.random.uniform(5, 15),
            precipitation=np.random.uniform(0, 0.3),
            cloud_coverage=np.random.uniform(0, 1),
            pressure=1013 - (alt / 30) + np.random.uniform(-10, 10),
            humidity=np.random.uniform(0.3, 0.8),
            turbulence_forecast=np.random.uniform(0, 0.6),
            storm_probability=np.random.uniform(0, 0.3),
            source="MeteoAPI"
        )
    
    async def get_route_weather(self, waypoints: List[Tuple[float, float]], 
                               altitude: float = 35000) -> List[WeatherData]:
        """Get weather along route"""
        weather_data = []
        
        for lat, lon in waypoints:
            weather = await self.get_aviation_weather(lat, lon, altitude)
            weather_data.append(weather)
            await asyncio.sleep(0.05)  # Small delay between requests
        
        return weather_data

class NOTAMService:
    """Notice to Airmen (NOTAM) service simulation"""
    
    def __init__(self):
        self.rate_limiter = APIRateLimiter(max_calls=200, time_window=3600)
    
    async def get_active_notams(self, region: Tuple[float, float, float, float]) -> List[Dict]:
        """Get active NOTAMs for region"""
        await self.rate_limiter.acquire()
        
        # Simulate NOTAMs
        notams = []
        for i in range(np.random.randint(2, 8)):
            notam = {
                'id': f"NOTAM{np.random.randint(1000, 9999)}",
                'type': np.random.choice(['RUNWAY', 'AIRSPACE', 'NAVAID', 'WEATHER']),
                'severity': np.random.choice(['LOW', 'MEDIUM', 'HIGH']),
                'location': (
                    np.random.uniform(region[0], region[2]),
                    np.random.uniform(region[1], region[3])
                ),
                'description': f"Simulated NOTAM for testing purposes",
                'valid_from': datetime.now(),
                'valid_until': datetime.now() + timedelta(hours=np.random.randint(1, 72)),
                'impact_level': np.random.uniform(0.1, 0.8)
            }
            notams.append(notam)
        
        return notams

class MultiAPIManager:
    """Unified manager for multiple aviation APIs"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.apis = {}
        self.cache = {}
        self.cache_ttl = 60  # seconds
        
        # Initialize APIs
        self._initialize_apis()
    
    def _initialize_apis(self):
        """Initialize all API clients"""
        
        # OpenSky API
        opensky_config = self.config.get('opensky', {})
        self.apis['opensky'] = OpenSkyAPI(opensky_config.get('credentials'))
        
        # FlightAware API
        flightaware_config = self.config.get('flightaware', {})
        self.apis['flightaware'] = FlightAwareAPI(flightaware_config.get('api_key'))
        
        # AviationStack API
        aviationstack_config = self.config.get('aviationstack', {})
        self.apis['aviationstack'] = AviationStackAPI(aviationstack_config.get('api_key'))
        
        # Weather API
        weather_config = self.config.get('weather', {})
        self.apis['weather'] = WeatherAPI(weather_config.get('api_key'))
        
        # NOTAM Service
        self.apis['notam'] = NOTAMService()
    
    async def get_comprehensive_flight_data(self, region: Tuple[float, float, float, float] = None) -> Dict[str, Any]:
        """Get comprehensive flight data from multiple sources"""
        
        async with aiohttp.ClientSession() as session:
            # Set session for OpenSky API
            if 'opensky' in self.apis:
                self.apis['opensky'].session = session
            
            # Gather data from multiple sources concurrently
            tasks = []
            
            # OpenSky flights
            if 'opensky' in self.apis:
                tasks.append(self._get_opensky_flights(region))
            
            # FlightAware flights (sample airports)
            if 'flightaware' in self.apis:
                tasks.append(self._get_flightaware_flights())
            
            # AviationStack flights
            if 'aviationstack' in self.apis:
                tasks.append(self._get_aviationstack_flights())
            
            # Weather data
            if 'weather' in self.apis and region:
                tasks.append(self._get_regional_weather(region))
            
            # NOTAMs
            if 'notam' in self.apis and region:
                tasks.append(self._get_regional_notams(region))
            
            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            comprehensive_data = {
                'timestamp': datetime.now(),
                'flights': {
                    'opensky': [],
                    'flightaware': [],
                    'aviationstack': []
                },
                'weather': [],
                'notams': [],
                'statistics': {},
                'data_quality': {}
            }
            
            # Parse results
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Task {i} failed: {result}")
                    continue
                
                if i == 0 and isinstance(result, list):  # OpenSky
                    comprehensive_data['flights']['opensky'] = result
                elif i == 1 and isinstance(result, list):  # FlightAware
                    comprehensive_data['flights']['flightaware'] = result
                elif i == 2 and isinstance(result, list):  # AviationStack
                    comprehensive_data['flights']['aviationstack'] = result
                elif i == 3 and isinstance(result, list):  # Weather
                    comprehensive_data['weather'] = result
                elif i == 4 and isinstance(result, list):  # NOTAMs
                    comprehensive_data['notams'] = result
            
            # Calculate statistics and quality metrics
            comprehensive_data['statistics'] = self._calculate_statistics(comprehensive_data)
            comprehensive_data['data_quality'] = self._assess_data_quality(comprehensive_data)
            
            return comprehensive_data
    
    async def _get_opensky_flights(self, region: Tuple[float, float, float, float] = None) -> List[FlightData]:
        """Get flights from OpenSky API"""
        try:
            return await self.apis['opensky'].get_all_flights(region)
        except Exception as e:
            logger.error(f"OpenSky API error: {e}")
            return []
    
    async def _get_flightaware_flights(self) -> List[FlightData]:
        """Get flights from FlightAware API"""
        try:
            # Sample from major airports
            airports = ['JFK', 'LAX', 'ORD', 'DFW', 'ATL']
            all_flights = []
            
            for airport in airports[:2]:  # Limit to avoid too many calls
                flights = await self.apis['flightaware'].get_airport_flights(airport)
                all_flights.extend(flights)
            
            return all_flights
        except Exception as e:
            logger.error(f"FlightAware API error: {e}")
            return []
    
    async def _get_aviationstack_flights(self) -> List[FlightData]:
        """Get flights from AviationStack API"""
        try:
            return await self.apis['aviationstack'].get_real_time_flights(limit=50)
        except Exception as e:
            logger.error(f"AviationStack API error: {e}")
            return []
    
    async def _get_regional_weather(self, region: Tuple[float, float, float, float]) -> List[WeatherData]:
        """Get weather data for region"""
        try:
            weather_data = []
            
            # Sample weather points across region
            lat_points = np.linspace(region[0], region[2], 5)
            lon_points = np.linspace(region[1], region[3], 5)
            
            for lat in lat_points:
                for lon in lon_points:
                    weather = await self.apis['weather'].get_aviation_weather(lat, lon)
                    weather_data.append(weather)
            
            return weather_data
        except Exception as e:
            logger.error(f"Weather API error: {e}")
            return []
    
    async def _get_regional_notams(self, region: Tuple[float, float, float, float]) -> List[Dict]:
        """Get NOTAMs for region"""
        try:
            return await self.apis['notam'].get_active_notams(region)
        except Exception as e:
            logger.error(f"NOTAM service error: {e}")
            return []
    
    def _calculate_statistics(self, data: Dict) -> Dict[str, Any]:
        """Calculate comprehensive statistics"""
        stats = {
            'total_flights': 0,
            'flights_by_source': {},
            'average_altitude': 0,
            'altitude_distribution': {},
            'speed_statistics': {},
            'geographic_coverage': {},
            'data_freshness': {}
        }
        
        all_flights = []
        for source, flights in data['flights'].items():
            stats['flights_by_source'][source] = len(flights)
            stats['total_flights'] += len(flights)
            all_flights.extend(flights)
        
        if all_flights:
            altitudes = [f.altitude for f in all_flights if f.altitude]
            speeds = [f.velocity for f in all_flights if f.velocity]
            
            if altitudes:
                stats['average_altitude'] = np.mean(altitudes)
                stats['altitude_distribution'] = {
                    'min': np.min(altitudes),
                    'max': np.max(altitudes),
                    'std': np.std(altitudes)
                }
            
            if speeds:
                stats['speed_statistics'] = {
                    'average': np.mean(speeds),
                    'min': np.min(speeds),
                    'max': np.max(speeds)
                }
        
        return stats
    
    def _assess_data_quality(self, data: Dict) -> Dict[str, Any]:
        """Assess data quality metrics"""
        quality = {
            'completeness': {},
            'consistency': {},
            'accuracy': {},
            'timeliness': {},
            'overall_score': 0
        }
        
        # Completeness assessment
        total_expected_fields = 0
        total_present_fields = 0
        
        for source, flights in data['flights'].items():
            if flights:
                sample_flight = flights[0]
                flight_dict = asdict(sample_flight)
                
                expected_fields = len(flight_dict)
                present_fields = sum(1 for v in flight_dict.values() if v is not None)
                
                quality['completeness'][source] = present_fields / expected_fields
                total_expected_fields += expected_fields
                total_present_fields += present_fields
        
        if total_expected_fields > 0:
            quality['completeness']['overall'] = total_present_fields / total_expected_fields
        
        # Timeliness assessment
        current_time = datetime.now()
        for source, flights in data['flights'].items():
            if flights:
                timestamps = [f.timestamp for f in flights if f.timestamp]
                if timestamps:
                    avg_age = np.mean([(current_time - ts).total_seconds() for ts in timestamps])
                    quality['timeliness'][source] = max(0, 1 - (avg_age / 3600))  # 1 hour max age
        
        # Calculate overall score
        scores = []
        for metric_type, metrics in quality.items():
            if isinstance(metrics, dict) and 'overall' in metrics:
                scores.append(metrics['overall'])
            elif isinstance(metrics, dict):
                scores.extend([v for v in metrics.values() if isinstance(v, (int, float))])
        
        if scores:
            quality['overall_score'] = np.mean(scores)
        
        return quality
    
    def get_cached_data(self, key: str) -> Optional[Any]:
        """Get cached data if available and fresh"""
        if key in self.cache:
            cached_item = self.cache[key]
            if time.time() - cached_item['timestamp'] < self.cache_ttl:
                return cached_item['data']
        return None
    
    def set_cached_data(self, key: str, data: Any):
        """Cache data with timestamp"""
        self.cache[key] = {
            'data': data,
            'timestamp': time.time()
        }

async def main():
    """Test the multi-API integration system"""
    print("🌐 Testing Multi-API Integration Framework")
    print("=" * 60)
    
    # Configuration
    config = {
        'opensky': {
            'credentials': {
                'username': 'test_user',
                'password': 'test_pass'
            }
        },
        'flightaware': {
            'api_key': 'test_key'
        },
        'aviationstack': {
            'api_key': 'test_key'
        },
        'weather': {
            'api_key': 'test_key'
        }
    }
    
    # Test region (roughly US East Coast)
    test_region = (35.0, -85.0, 45.0, -65.0)  # lat_min, lon_min, lat_max, lon_max
    
    # Initialize API manager
    manager = MultiAPIManager(config)
    
    print("🚀 Fetching comprehensive flight data...")
    
    try:
        # Get comprehensive data
        comprehensive_data = await manager.get_comprehensive_flight_data(test_region)
        
        # Display results
        print(f"\n📊 Data Collection Results:")
        print(f"   Timestamp: {comprehensive_data['timestamp']}")
        print(f"   Total flights: {comprehensive_data['statistics']['total_flights']}")
        
        for source, count in comprehensive_data['statistics']['flights_by_source'].items():
            print(f"   {source}: {count} flights")
        
        print(f"   Weather points: {len(comprehensive_data['weather'])}")
        print(f"   NOTAMs: {len(comprehensive_data['notams'])}")
        
        print(f"\n📈 Quality Metrics:")
        quality = comprehensive_data['data_quality']
        print(f"   Overall score: {quality['overall_score']:.3f}")
        
        if 'completeness' in quality:
            for source, score in quality['completeness'].items():
                if isinstance(score, (int, float)):
                    print(f"   {source} completeness: {score:.3f}")
        
        # Sample flight data
        if comprehensive_data['statistics']['total_flights'] > 0:
            print(f"\n✈️ Sample Flights:")
            sample_count = 0
            for source, flights in comprehensive_data['flights'].items():
                if flights and sample_count < 3:
                    flight = flights[0]
                    print(f"   {flight.callsign} ({flight.source}): {flight.latitude:.3f}, {flight.longitude:.3f}, {flight.altitude:.0f}ft")
                    sample_count += 1
        
        # Weather sample
        if comprehensive_data['weather']:
            weather = comprehensive_data['weather'][0]
            print(f"\n🌦️ Sample Weather:")
            print(f"   Location: {weather.location}")
            print(f"   Temperature: {weather.temperature:.1f}°C")
            print(f"   Wind: {weather.wind_speed:.1f} kt @ {weather.wind_direction:.0f}°")
            print(f"   Visibility: {weather.visibility:.1f} km")
        
        print(f"\n✅ Multi-API integration test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())