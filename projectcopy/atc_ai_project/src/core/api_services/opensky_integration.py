#!/usr/bin/env python3
"""
OpenSky Network API Integration
FREE real-time flight data integration
"""

import requests
import json
import time
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class FlightData:
    """Flight data structure from OpenSky"""
    icao24: str
    callsign: str
    origin_country: str
    time_position: int
    last_contact: int
    longitude: float
    latitude: float
    baro_altitude: float
    on_ground: bool
    velocity: float
    true_track: float
    vertical_rate: float
    sensors: List[int]
    geo_altitude: float
    squawk: str
    spi: bool
    position_source: int

class OpenSkyIntegration:
    """OpenSky Network API integration"""
    
    def __init__(self, username: str = None, password: str = None):
        self.base_url = "https://opensky-network.org/api"
        self.username = username
        self.password = password
        self.rate_limit_delay = 6  # 10 requests per minute = 6 seconds delay
        
        # API endpoints
        self.endpoints = {
            "all_states": "/states/all",
            "own_states": "/states/own",
            "aircraft": "/aircraft",
            "arrivals": "/flights/arrival",
            "departures": "/flights/departure",
            "track": "/tracks"
        }
        
        logger.info("OpenSky Integration initialized")
    
    def get_all_flights(self, bbox: Optional[Dict[str, float]] = None) -> List[FlightData]:
        """Get all flights in the system or within bounding box"""
        
        try:
            url = f"{self.base_url}{self.endpoints['all_states']}"
            
            # Add bounding box if provided (min_lon, max_lon, min_lat, max_lat)
            if bbox:
                params = {
                    "lamin": bbox["min_lat"],
                    "lomin": bbox["min_lon"],
                    "lamax": bbox["max_lat"],
                    "lomax": bbox["max_lon"]
                }
            else:
                params = {}
            
            # Add authentication if available
            auth = None
            if self.username and self.password:
                auth = (self.username, self.password)
            
            response = requests.get(url, params=params, auth=auth, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if "states" not in data:
                logger.warning("No flight states in response")
                return []
            
            flights = []
            for state in data["states"]:
                if len(state) >= 17:  # Ensure we have all required fields
                    flight = FlightData(
                        icao24=state[0] if state[0] else "UNKNOWN",
                        callsign=state[1].strip() if state[1] else "UNKNOWN",
                        origin_country=state[2] if state[2] else "UNKNOWN",
                        time_position=state[3] if state[3] else 0,
                        last_contact=state[4] if state[4] else 0,
                        longitude=state[5] if state[5] else 0.0,
                        latitude=state[6] if state[6] else 0.0,
                        baro_altitude=state[7] if state[7] else 0.0,
                        on_ground=state[8] if state[8] is not None else False,
                        velocity=state[9] if state[9] else 0.0,
                        true_track=state[10] if state[10] else 0.0,
                        vertical_rate=state[11] if state[11] else 0.0,
                        sensors=state[12] if state[12] else [],
                        geo_altitude=state[13] if state[13] else 0.0,
                        squawk=state[14] if state[14] else "UNKNOWN",
                        spi=state[15] if state[15] is not None else False,
                        position_source=state[16] if state[16] else 0
                    )
                    flights.append(flight)
            
            logger.info(f"Retrieved {len(flights)} flights from OpenSky")
            return flights
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching flights from OpenSky: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return []
    
    def get_flights_by_area(self, min_lat: float, max_lat: float, 
                           min_lon: float, max_lon: float) -> List[FlightData]:
        """Get flights within specific geographic area"""
        
        bbox = {
            "min_lat": min_lat,
            "max_lat": max_lat,
            "min_lon": min_lon,
            "max_lon": max_lon
        }
        
        return self.get_all_flights(bbox)
    
    def get_flights_by_airport(self, airport_lat: float, airport_lon: float, 
                              radius_km: float = 50) -> List[FlightData]:
        """Get flights near specific airport"""
        
        # Convert radius to degrees (approximate)
        lat_radius = radius_km / 111.0  # 1 degree ≈ 111 km
        lon_radius = radius_km / (111.0 * abs(math.cos(math.radians(airport_lat))))
        
        min_lat = airport_lat - lat_radius
        max_lat = airport_lat + lat_radius
        min_lon = airport_lon - lon_radius
        max_lon = airport_lon + lon_radius
        
        return self.get_flights_by_area(min_lat, max_lat, min_lon, max_lon)
    
    def get_flight_track(self, icao24: str, start_time: int, end_time: int) -> List[Dict[str, Any]]:
        """Get track history for specific aircraft"""
        
        try:
            url = f"{self.base_url}{self.endpoints['track']}"
            params = {
                "icao24": icao24,
                "time": start_time,
                "end": end_time
            }
            
            auth = None
            if self.username and self.password:
                auth = (self.username, self.password)
            
            response = requests.get(url, params=params, auth=auth, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if "path" not in data:
                logger.warning(f"No track data for aircraft {icao24}")
                return []
            
            track_points = []
            for point in data["path"]:
                if len(point) >= 4:
                    track_points.append({
                        "timestamp": point[0],
                        "latitude": point[1],
                        "longitude": point[2],
                        "altitude": point[3]
                    })
            
            logger.info(f"Retrieved {len(track_points)} track points for {icao24}")
            return track_points
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching track for {icao24}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return []
    
    def get_aircraft_info(self, icao24: str) -> Optional[Dict[str, Any]]:
        """Get aircraft information"""
        
        try:
            url = f"{self.base_url}{self.endpoints['aircraft']}"
            params = {"icao24": icao24}
            
            auth = None
            if self.username and self.password:
                auth = (self.username, self.password)
            
            response = requests.get(url, params=params, auth=auth, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if not data:
                logger.warning(f"No aircraft info for {icao24}")
                return None
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching aircraft info for {icao24}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None
    
    def get_arrivals(self, airport: str, begin: int, end: int) -> List[Dict[str, Any]]:
        """Get arrivals for specific airport"""
        
        try:
            url = f"{self.base_url}{self.endpoints['arrivals']}"
            params = {
                "airport": airport,
                "begin": begin,
                "end": end
            }
            
            auth = None
            if self.username and self.password:
                auth = (self.username, self.password)
            
            response = requests.get(url, params=params, auth=auth, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            logger.info(f"Retrieved {len(data)} arrivals for {airport}")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching arrivals for {airport}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return []
    
    def get_departures(self, airport: str, begin: int, end: int) -> List[Dict[str, Any]]:
        """Get departures for specific airport"""
        
        try:
            url = f"{self.base_url}{self.endpoints['departures']}"
            params = {
                "airport": airport,
                "begin": begin,
                "end": end
            }
            
            auth = None
            if self.username and self.password:
                auth = (self.username, self.password)
            
            response = requests.get(url, params=params, auth=auth, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            logger.info(f"Retrieved {len(data)} departures for {airport}")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching departures for {airport}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return []
    
    def convert_to_aircraft_format(self, flight: FlightData) -> Dict[str, Any]:
        """Convert OpenSky flight data to our Aircraft format"""
        
        return {
            "icao24": flight.icao24,
            "callsign": flight.callsign,
            "latitude": flight.latitude,
            "longitude": flight.longitude,
            "altitude": flight.baro_altitude if flight.baro_altitude else flight.geo_altitude,
            "velocity": flight.velocity,
            "heading": flight.true_track,
            "vertical_rate": flight.vertical_rate,
            "timestamp": datetime.fromtimestamp(flight.last_contact),
            "aircraft_type": "UNKNOWN",
            "priority": 1,
            "on_ground": flight.on_ground,
            "squawk": flight.squawk,
            "origin_country": flight.origin_country
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get OpenSky integration status"""
        
        return {
            "service": "OpenSky Network",
            "status": "operational",
            "authenticated": bool(self.username and self.password),
            "rate_limit_delay": self.rate_limit_delay,
            "endpoints": list(self.endpoints.keys()),
            "last_update": datetime.now().isoformat()
        }

def main():
    """Test OpenSky integration"""
    
    # Initialize OpenSky integration
    opensky = OpenSkyIntegration()
    
    # Test without authentication (limited data)
    print("Testing OpenSky integration...")
    
    # Get flights in New York area
    flights = opensky.get_flights_by_area(
        min_lat=40.0, max_lat=41.0,
        min_lon=-75.0, max_lon=-73.0
    )
    
    print(f"Found {len(flights)} flights in New York area")
    
    for flight in flights[:5]:  # Show first 5 flights
        print(f"Flight: {flight.callsign} ({flight.icao24})")
        print(f"Position: {flight.latitude:.4f}, {flight.longitude:.4f}")
        print(f"Altitude: {flight.baro_altitude:.0f} ft")
        print(f"Speed: {flight.velocity:.0f} knots")
        print(f"Track: {flight.true_track:.0f}°")
        print()
    
    # Get system status
    status = opensky.get_system_status()
    print("System Status:")
    print(f"Service: {status['service']}")
    print(f"Status: {status['status']}")
    print(f"Authenticated: {status['authenticated']}")

if __name__ == "__main__":
    import math
    main()
