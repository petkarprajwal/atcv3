"""
OpenSky Network API Service

This module provides a comprehensive service wrapper for the OpenSky Network API
with rate limiting, retry logic, caching, and comprehensive error handling.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union, Tuple
import requests
import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from cachetools import TTLCache
import json

from config.opensky_config import get_config, OpenSkyConfig
from models.opensky_models import (
    StateVector, OpenSkyStates, FlightData, FlightTrack, 
    Waypoint, BoundingBox, APIError, APIResponse
)
from utils.opensky_utils import (
    validate_icao24, normalize_icao24, validate_icao_airport,
    normalize_icao_airport, parse_opensky_raw_state, parse_opensky_raw_waypoint
)


class RateLimiter:
    """Simple rate limiter for API requests"""
    
    def __init__(self, min_interval: float):
        self.min_interval = min_interval
        self.last_request_time = 0.0
    
    def wait_if_needed(self):
        """Wait if necessary to respect rate limit"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_interval:
            sleep_time = self.min_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()


class OpenSkyAPIException(Exception):
    """Custom exception for OpenSky API errors"""
    
    def __init__(self, message: str, status_code: Optional[int] = None, 
                 response_data: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class OpenSkyService:
    """
    Comprehensive OpenSky Network API service wrapper
    
    Features:
    - Rate limiting for authenticated and unauthenticated requests
    - Automatic retry logic with exponential backoff
    - Response caching to minimize API calls
    - Comprehensive error handling
    - Both synchronous and asynchronous methods
    - Data validation and type conversion
    """
    
    def __init__(self, config: Optional[OpenSkyConfig] = None):
        """
        Initialize OpenSky service
        
        Args:
            config: OpenSky configuration (uses global config if None)
        """
        self.config = config or get_config()
        self.logger = logging.getLogger(f"opensky_service.{self.config.environment}")
        
        # Setup rate limiter
        self.rate_limiter = RateLimiter(self.config.get_rate_limit())
        
        # Setup cache
        self.cache = TTLCache(
            maxsize=self.config.api_config.max_cache_size,
            ttl=self.config.api_config.cache_ttl
        )
        
        # Setup session
        self.session = requests.Session()
        if self.config.is_authenticated:
            auth = self.config.get_auth_tuple()
            self.session.auth = auth
            self.logger.info("Initialized with authentication")
        else:
            self.logger.info("Initialized without authentication")
    
    def _make_cache_key(self, endpoint: str, params: Dict[str, Any]) -> str:
        """Generate cache key for request"""
        param_str = "&".join(f"{k}={v}" for k, v in sorted(params.items()) if v is not None)
        return f"{endpoint}?{param_str}"
    
    def _handle_response(self, response: requests.Response, 
                        start_time: float) -> APIResponse:
        """
        Handle API response and convert to APIResponse object
        
        Args:
            response: requests Response object
            start_time: Request start time for timing
            
        Returns:
            APIResponse object
        """
        response_time = time.time() - start_time
        
        try:
            if response.status_code == 200:
                data = response.json()
                return APIResponse(
                    success=True,
                    data=data,
                    status_code=response.status_code,
                    response_time=response_time
                )
            else:
                error_data = {}
                try:
                    error_data = response.json()
                except:
                    error_data = {"message": response.text}
                
                error = APIError(**error_data)
                return APIResponse(
                    success=False,
                    error=error,
                    status_code=response.status_code,
                    response_time=response_time
                )
                
        except Exception as e:
            self.logger.error(f"Error handling response: {e}")
            error = APIError(
                status=response.status_code,
                message=f"Response processing error: {str(e)}"
            )
            return APIResponse(
                success=False,
                error=error,
                status_code=response.status_code,
                response_time=response_time
            )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((requests.RequestException, requests.Timeout))
    )
    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> APIResponse:
        """
        Make HTTP request with retry logic and rate limiting
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            APIResponse object
        """
        params = params or {}
        
        # Check cache first
        cache_key = self._make_cache_key(endpoint, params)
        if cache_key in self.cache:
            self.logger.debug(f"Cache hit for {endpoint}")
            return self.cache[cache_key]
        
        # Apply rate limiting
        self.rate_limiter.wait_if_needed()
        
        # Make request
        url = f"{self.config.api_config.base_url}/{endpoint}"
        start_time = time.time()
        
        try:
            self.logger.debug(f"Making request to {url} with params: {params}")
            
            response = self.session.get(
                url,
                params=params,
                timeout=self.config.api_config.timeout
            )
            
            api_response = self._handle_response(response, start_time)
            
            # Cache successful responses
            if api_response.success:
                self.cache[cache_key] = api_response
            
            return api_response
            
        except requests.RequestException as e:
            self.logger.error(f"Request failed: {e}")
            raise
    
    def get_current_states(self, 
                          bbox: Optional[BoundingBox] = None,
                          icao24: Optional[Union[str, List[str]]] = None) -> OpenSkyStates:
        """
        Retrieve current aircraft states
        
        Args:
            bbox: Geographic bounding box for filtering
            icao24: Specific aircraft ICAO24 address(es)
            
        Returns:
            OpenSkyStates object with current aircraft states
            
        Raises:
            OpenSkyAPIException: If API request fails
        """
        params = {}
        
        if bbox:
            params['lamin'] = bbox.min_latitude
            params['lomin'] = bbox.min_longitude
            params['lamax'] = bbox.max_latitude
            params['lomax'] = bbox.max_longitude
        
        if icao24:
            if isinstance(icao24, str):
                icao24 = [icao24]
            # Validate and normalize ICAO24 addresses
            normalized_icao24 = [normalize_icao24(addr) for addr in icao24]
            params['icao24'] = ','.join(normalized_icao24)
        
        response = self._make_request("states/all", params)
        
        if not response.success:
            raise OpenSkyAPIException(
                f"Failed to get current states: {response.error}",
                response.status_code,
                response.error.dict() if response.error else None
            )
        
        data = response.data
        states = []
        
        if data.get('states'):
            for raw_state in data['states']:
                try:
                    state = parse_opensky_raw_state(raw_state)
                    states.append(state)
                except Exception as e:
                    self.logger.warning(f"Failed to parse state: {e}")
        
        return OpenSkyStates(
            time=data.get('time', int(time.time())),
            states=states
        )
    
    def get_my_sensor_states(self, 
                            icao24: Optional[Union[str, List[str]]] = None,
                            serials: Optional[List[int]] = None) -> OpenSkyStates:
        """
        Retrieve states from user's own sensors (requires authentication)
        
        Args:
            icao24: Specific aircraft ICAO24 address(es)
            serials: Specific sensor serial numbers
            
        Returns:
            OpenSkyStates object
            
        Raises:
            OpenSkyAPIException: If not authenticated or request fails
        """
        if not self.config.is_authenticated:
            raise OpenSkyAPIException("Authentication required for sensor data")
        
        params = {}
        
        if icao24:
            if isinstance(icao24, str):
                icao24 = [icao24]
            normalized_icao24 = [normalize_icao24(addr) for addr in icao24]
            params['icao24'] = ','.join(normalized_icao24)
        
        if serials:
            params['serials'] = ','.join(map(str, serials))
        
        response = self._make_request("states/own", params)
        
        if not response.success:
            raise OpenSkyAPIException(
                f"Failed to get sensor states: {response.error}",
                response.status_code
            )
        
        data = response.data
        states = []
        
        if data.get('states'):
            for raw_state in data['states']:
                try:
                    state = parse_opensky_raw_state(raw_state)
                    states.append(state)
                except Exception as e:
                    self.logger.warning(f"Failed to parse state: {e}")
        
        return OpenSkyStates(
            time=data.get('time', int(time.time())),
            states=states
        )
    
    def get_flights_in_timerange(self, begin: int, end: int) -> List[FlightData]:
        """
        Retrieve flights in time range (max 2 hours)
        
        Args:
            begin: Start time (Unix timestamp)
            end: End time (Unix timestamp)
            
        Returns:
            List of FlightData objects
            
        Raises:
            OpenSkyAPIException: If time range too large or request fails
        """
        # Validate time range (max 2 hours = 7200 seconds)
        if end - begin > 7200:
            raise OpenSkyAPIException("Time range cannot exceed 2 hours")
        
        params = {
            'begin': begin,
            'end': end
        }
        
        response = self._make_request("flights/all", params)
        
        if not response.success:
            raise OpenSkyAPIException(
                f"Failed to get flights in timerange: {response.error}",
                response.status_code
            )
        
        flights = []
        for flight_data in response.data:
            try:
                flight = FlightData(**flight_data)
                flights.append(flight)
            except Exception as e:
                self.logger.warning(f"Failed to parse flight data: {e}")
        
        return flights
    
    def get_aircraft_flights(self, icao24: str, begin: int, end: int) -> List[FlightData]:
        """
        Retrieve flights for specific aircraft (max 30 days)
        
        Args:
            icao24: Aircraft ICAO24 address
            begin: Start time (Unix timestamp)
            end: End time (Unix timestamp)
            
        Returns:
            List of FlightData objects
            
        Raises:
            OpenSkyAPIException: If time range too large or request fails
        """
        # Validate time range (max 30 days = 2592000 seconds)
        if end - begin > 2592000:
            raise OpenSkyAPIException("Time range cannot exceed 30 days")
        
        icao24 = normalize_icao24(icao24)
        
        params = {
            'icao24': icao24,
            'begin': begin,
            'end': end
        }
        
        response = self._make_request("flights/aircraft", params)
        
        if not response.success:
            raise OpenSkyAPIException(
                f"Failed to get aircraft flights: {response.error}",
                response.status_code
            )
        
        flights = []
        for flight_data in response.data:
            try:
                flight = FlightData(**flight_data)
                flights.append(flight)
            except Exception as e:
                self.logger.warning(f"Failed to parse flight data: {e}")
        
        return flights
    
    def get_airport_arrivals(self, airport_icao: str, begin: int, end: int) -> List[FlightData]:
        """
        Retrieve arrivals for specific airport (max 7 days)
        
        Args:
            airport_icao: Airport ICAO code
            begin: Start time (Unix timestamp)
            end: End time (Unix timestamp)
            
        Returns:
            List of FlightData objects
            
        Raises:
            OpenSkyAPIException: If time range too large or request fails
        """
        # Validate time range (max 7 days = 604800 seconds)
        if end - begin > 604800:
            raise OpenSkyAPIException("Time range cannot exceed 7 days")
        
        airport_icao = normalize_icao_airport(airport_icao)
        
        params = {
            'airport': airport_icao,
            'begin': begin,
            'end': end
        }
        
        response = self._make_request("flights/arrival", params)
        
        if not response.success:
            raise OpenSkyAPIException(
                f"Failed to get airport arrivals: {response.error}",
                response.status_code
            )
        
        flights = []
        for flight_data in response.data:
            try:
                flight = FlightData(**flight_data)
                flights.append(flight)
            except Exception as e:
                self.logger.warning(f"Failed to parse flight data: {e}")
        
        return flights
    
    def get_airport_departures(self, airport_icao: str, begin: int, end: int) -> List[FlightData]:
        """
        Retrieve departures for specific airport (max 7 days)
        
        Args:
            airport_icao: Airport ICAO code
            begin: Start time (Unix timestamp)
            end: End time (Unix timestamp)
            
        Returns:
            List of FlightData objects
            
        Raises:
            OpenSkyAPIException: If time range too large or request fails
        """
        # Validate time range (max 7 days = 604800 seconds)
        if end - begin > 604800:
            raise OpenSkyAPIException("Time range cannot exceed 7 days")
        
        airport_icao = normalize_icao_airport(airport_icao)
        
        params = {
            'airport': airport_icao,
            'begin': begin,
            'end': end
        }
        
        response = self._make_request("flights/departure", params)
        
        if not response.success:
            raise OpenSkyAPIException(
                f"Failed to get airport departures: {response.error}",
                response.status_code
            )
        
        flights = []
        for flight_data in response.data:
            try:
                flight = FlightData(**flight_data)
                flights.append(flight)
            except Exception as e:
                self.logger.warning(f"Failed to parse flight data: {e}")
        
        return flights
    
    def get_aircraft_track(self, icao24: str, timestamp: int = 0) -> FlightTrack:
        """
        Retrieve aircraft trajectory (0 for live track)
        
        Args:
            icao24: Aircraft ICAO24 address
            timestamp: Unix timestamp (0 for live)
            
        Returns:
            FlightTrack object
            
        Raises:
            OpenSkyAPIException: If request fails
        """
        icao24 = normalize_icao24(icao24)
        
        params = {
            'icao24': icao24,
            'time': timestamp
        }
        
        response = self._make_request("tracks/all", params)
        
        if not response.success:
            raise OpenSkyAPIException(
                f"Failed to get aircraft track: {response.error}",
                response.status_code
            )
        
        data = response.data
        waypoints = []
        
        if data.get('path'):
            for raw_waypoint in data['path']:
                try:
                    waypoint = parse_opensky_raw_waypoint(raw_waypoint)
                    waypoints.append(waypoint)
                except Exception as e:
                    self.logger.warning(f"Failed to parse waypoint: {e}")
        
        # Determine start and end times
        start_time = waypoints[0].time if waypoints else timestamp
        end_time = waypoints[-1].time if waypoints else timestamp
        
        return FlightTrack(
            icao24=icao24,
            callsign=data.get('callsign'),
            start_time=start_time,
            end_time=end_time,
            waypoints=waypoints
        )
    
    def clear_cache(self):
        """Clear the response cache"""
        self.cache.clear()
        self.logger.info("Response cache cleared")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'cache_size': len(self.cache),
            'max_size': self.cache.maxsize,
            'ttl': self.cache.ttl
        }
    
    def close(self):
        """Close the session and cleanup resources"""
        self.session.close()
        self.clear_cache()
        self.logger.info("OpenSky service closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()