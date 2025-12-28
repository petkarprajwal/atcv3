"""
Data models for OpenSky Network API integration

This module defines Pydantic models for representing OpenSky API data structures
including aircraft states, flight data, trajectories, and geographic areas.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass
from pydantic import BaseModel, Field, validator, root_validator
import math


class BoundingBox(BaseModel):
    """
    Geographic bounding box for filtering aircraft states
    
    Coordinates in WGS-84 decimal degrees
    """
    min_latitude: float = Field(..., ge=-90, le=90, description="Minimum latitude")
    max_latitude: float = Field(..., ge=-90, le=90, description="Maximum latitude")
    min_longitude: float = Field(..., ge=-180, le=180, description="Minimum longitude")
    max_longitude: float = Field(..., ge=-180, le=180, description="Maximum longitude")
    
    @validator('max_latitude')
    def validate_latitude_range(cls, v, values):
        if 'min_latitude' in values and v <= values['min_latitude']:
            raise ValueError('max_latitude must be greater than min_latitude')
        return v
    
    @validator('max_longitude')
    def validate_longitude_range(cls, v, values):
        if 'min_longitude' in values and v <= values['min_longitude']:
            raise ValueError('max_longitude must be greater than min_longitude')
        return v
    
    def contains_point(self, latitude: float, longitude: float) -> bool:
        """Check if a point is within this bounding box"""
        return (self.min_latitude <= latitude <= self.max_latitude and
                self.min_longitude <= longitude <= self.max_longitude)
    
    def to_opensky_format(self) -> str:
        """Convert to OpenSky API format: lamin,lomin,lamax,lomax"""
        return f"{self.min_latitude},{self.min_longitude},{self.max_latitude},{self.max_longitude}"


class StateVector(BaseModel):
    """
    Aircraft state vector from OpenSky Network
    
    Represents the state of an aircraft at a specific time
    """
    icao24: str = Field(..., description="Unique ICAO 24-bit address")
    callsign: Optional[str] = Field(None, description="Aircraft callsign")
    origin_country: Optional[str] = Field(None, description="Country of registration")
    time_position: Optional[int] = Field(None, description="Unix timestamp of position")
    last_contact: Optional[int] = Field(None, description="Unix timestamp of last contact")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude in degrees")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude in degrees")
    baro_altitude: Optional[float] = Field(None, description="Barometric altitude in meters")
    on_ground: Optional[bool] = Field(None, description="Whether aircraft is on ground")
    velocity: Optional[float] = Field(None, ge=0, description="Ground speed in m/s")
    true_track: Optional[float] = Field(None, ge=0, lt=360, description="True track in degrees")
    vertical_rate: Optional[float] = Field(None, description="Vertical rate in m/s")
    sensors: Optional[List[int]] = Field(None, description="Sensor serial numbers")
    geo_altitude: Optional[float] = Field(None, description="Geometric altitude in meters")
    squawk: Optional[str] = Field(None, description="Transponder code")
    spi: Optional[bool] = Field(None, description="Special position identification")
    position_source: Optional[int] = Field(None, description="Position source type")
    
    @validator('icao24')
    def validate_icao24(cls, v):
        if v and not v.islower():
            v = v.lower()
        if v and len(v) != 6:
            raise ValueError('ICAO24 address must be 6 characters long')
        if v and not all(c in '0123456789abcdef' for c in v):
            raise ValueError('ICAO24 address must be hexadecimal')
        return v
    
    @validator('callsign')
    def clean_callsign(cls, v):
        return v.strip() if v else None
    
    @property
    def has_position(self) -> bool:
        """Check if state vector has valid position data"""
        return self.latitude is not None and self.longitude is not None
    
    @property
    def position_age_seconds(self) -> Optional[float]:
        """Get age of position data in seconds"""
        if self.time_position and self.last_contact:
            return self.last_contact - self.time_position
        return None
    
    def distance_to(self, other: 'StateVector') -> Optional[float]:
        """
        Calculate distance to another state vector in kilometers
        Uses Haversine formula
        """
        if not (self.has_position and other.has_position):
            return None
        
        lat1, lon1 = math.radians(self.latitude), math.radians(self.longitude)
        lat2, lon2 = math.radians(other.latitude), math.radians(other.longitude)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = (math.sin(dlat/2)**2 + 
             math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2)
        c = 2 * math.asin(math.sqrt(a))
        
        return 6371 * c  # Earth radius in km


class OpenSkyStates(BaseModel):
    """
    Collection of aircraft states with timestamp
    """
    time: int = Field(..., description="Unix timestamp when data was retrieved")
    states: List[StateVector] = Field(default_factory=list, description="List of aircraft states")
    
    @property
    def aircraft_count(self) -> int:
        """Get number of aircraft in this state collection"""
        return len(self.states)
    
    def filter_by_bbox(self, bbox: BoundingBox) -> 'OpenSkyStates':
        """Filter states by bounding box"""
        filtered_states = [
            state for state in self.states
            if state.has_position and bbox.contains_point(state.latitude, state.longitude)
        ]
        return OpenSkyStates(time=self.time, states=filtered_states)
    
    def filter_by_country(self, country: str) -> 'OpenSkyStates':
        """Filter states by origin country"""
        filtered_states = [
            state for state in self.states
            if state.origin_country and state.origin_country.lower() == country.lower()
        ]
        return OpenSkyStates(time=self.time, states=filtered_states)
    
    def get_by_icao24(self, icao24: str) -> Optional[StateVector]:
        """Get state vector by ICAO24 address"""
        icao24 = icao24.lower()
        for state in self.states:
            if state.icao24 == icao24:
                return state
        return None


class Waypoint(BaseModel):
    """
    Single waypoint in an aircraft trajectory
    """
    time: int = Field(..., description="Unix timestamp")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude in degrees")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude in degrees")
    baro_altitude: Optional[float] = Field(None, description="Barometric altitude in meters")
    true_track: Optional[float] = Field(None, ge=0, lt=360, description="True track in degrees")
    on_ground: Optional[bool] = Field(None, description="Whether aircraft is on ground")
    
    @property
    def has_position(self) -> bool:
        """Check if waypoint has valid position data"""
        return self.latitude is not None and self.longitude is not None
    
    @property
    def datetime(self) -> datetime:
        """Convert timestamp to datetime object"""
        return datetime.fromtimestamp(self.time)


class FlightTrack(BaseModel):
    """
    Complete trajectory track for an aircraft
    """
    icao24: str = Field(..., description="Aircraft ICAO24 address")
    callsign: Optional[str] = Field(None, description="Aircraft callsign")
    start_time: int = Field(..., description="Track start time (Unix timestamp)")
    end_time: int = Field(..., description="Track end time (Unix timestamp)")
    waypoints: List[Waypoint] = Field(default_factory=list, description="Track waypoints")
    
    @validator('icao24')
    def validate_icao24(cls, v):
        return v.lower() if v else v
    
    @property
    def duration_seconds(self) -> int:
        """Get track duration in seconds"""
        return self.end_time - self.start_time
    
    @property
    def waypoint_count(self) -> int:
        """Get number of waypoints in track"""
        return len(self.waypoints)
    
    def get_position_waypoints(self) -> List[Waypoint]:
        """Get only waypoints with valid position data"""
        return [wp for wp in self.waypoints if wp.has_position]
    
    def get_bounding_box(self) -> Optional[BoundingBox]:
        """Calculate bounding box for this track"""
        position_waypoints = self.get_position_waypoints()
        if not position_waypoints:
            return None
        
        latitudes = [wp.latitude for wp in position_waypoints]
        longitudes = [wp.longitude for wp in position_waypoints]
        
        return BoundingBox(
            min_latitude=min(latitudes),
            max_latitude=max(latitudes),
            min_longitude=min(longitudes),
            max_longitude=max(longitudes)
        )


class FlightData(BaseModel):
    """
    Flight information including departure and arrival details
    """
    icao24: str = Field(..., description="Aircraft ICAO24 address")
    first_seen: int = Field(..., description="First seen timestamp")
    est_departure_airport: Optional[str] = Field(None, description="Estimated departure airport ICAO")
    last_seen: int = Field(..., description="Last seen timestamp")
    est_arrival_airport: Optional[str] = Field(None, description="Estimated arrival airport ICAO")
    callsign: Optional[str] = Field(None, description="Aircraft callsign")
    est_departure_airport_horiz_distance: Optional[int] = Field(
        None, description="Distance to departure airport in meters"
    )
    est_departure_airport_vert_distance: Optional[int] = Field(
        None, description="Vertical distance to departure airport in meters"
    )
    est_arrival_airport_horiz_distance: Optional[int] = Field(
        None, description="Distance to arrival airport in meters"
    )
    est_arrival_airport_vert_distance: Optional[int] = Field(
        None, description="Vertical distance to arrival airport in meters"
    )
    departure_airport_candidates_count: Optional[int] = Field(
        None, description="Number of departure airport candidates"
    )
    arrival_airport_candidates_count: Optional[int] = Field(
        None, description="Number of arrival airport candidates"
    )
    
    @validator('icao24')
    def validate_icao24(cls, v):
        return v.lower() if v else v
    
    @validator('callsign')
    def clean_callsign(cls, v):
        return v.strip() if v else None
    
    @property
    def flight_duration_seconds(self) -> int:
        """Get flight duration in seconds"""
        return self.last_seen - self.first_seen
    
    @property
    def departure_datetime(self) -> datetime:
        """Get departure datetime"""
        return datetime.fromtimestamp(self.first_seen)
    
    @property
    def arrival_datetime(self) -> datetime:
        """Get arrival datetime"""
        return datetime.fromtimestamp(self.last_seen)


class APIError(BaseModel):
    """
    OpenSky API error response
    """
    timestamp: Optional[int] = None
    status: Optional[int] = None
    error: Optional[str] = None
    message: Optional[str] = None
    path: Optional[str] = None
    
    def __str__(self) -> str:
        return f"OpenSky API Error {self.status}: {self.message}"


@dataclass
class APIResponse:
    """
    Generic API response wrapper
    """
    success: bool
    data: Optional[Any] = None
    error: Optional[APIError] = None
    status_code: Optional[int] = None
    response_time: Optional[float] = None
    
    @property
    def is_error(self) -> bool:
        return not self.success
    
    def __str__(self) -> str:
        if self.success:
            return f"Success: {type(self.data).__name__}"
        else:
            return f"Error: {self.error}"