"""
Utility functions for OpenSky Network API integration

This module provides helper functions for data validation, conversion,
and manipulation specific to OpenSky Network data.
"""

import re
import math
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Union, Tuple
import pandas as pd
from models.opensky_models import StateVector, BoundingBox, FlightData, Waypoint


# ICAO patterns
ICAO24_PATTERN = re.compile(r'^[0-9a-f]{6}$')
ICAO_AIRPORT_PATTERN = re.compile(r'^[A-Z]{4}$')


def datetime_to_unix(dt: datetime) -> int:
    """
    Convert datetime to Unix timestamp
    
    Args:
        dt: Datetime object (timezone-aware recommended)
        
    Returns:
        Unix timestamp as integer
    """
    if dt.tzinfo is None:
        # Assume UTC if no timezone specified
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


def unix_to_datetime(timestamp: int) -> datetime:
    """
    Convert Unix timestamp to datetime object
    
    Args:
        timestamp: Unix timestamp
        
    Returns:
        Timezone-aware datetime object in UTC
    """
    return datetime.fromtimestamp(timestamp, tz=timezone.utc)


def validate_icao24(icao24: str) -> bool:
    """
    Validate ICAO 24-bit address format
    
    Args:
        icao24: ICAO24 address string
        
    Returns:
        True if valid, False otherwise
    """
    if not icao24:
        return False
    return bool(ICAO24_PATTERN.match(icao24.lower()))


def normalize_icao24(icao24: str) -> str:
    """
    Normalize ICAO24 address to lowercase
    
    Args:
        icao24: ICAO24 address string
        
    Returns:
        Normalized ICAO24 address
        
    Raises:
        ValueError: If ICAO24 format is invalid
    """
    if not icao24:
        raise ValueError("ICAO24 address cannot be empty")
    
    normalized = icao24.lower().strip()
    if not validate_icao24(normalized):
        raise ValueError(f"Invalid ICAO24 address format: {icao24}")
    
    return normalized


def validate_icao_airport(airport_code: str) -> bool:
    """
    Validate ICAO airport code format
    
    Args:
        airport_code: ICAO airport code
        
    Returns:
        True if valid, False otherwise
    """
    if not airport_code:
        return False
    return bool(ICAO_AIRPORT_PATTERN.match(airport_code.upper()))


def normalize_icao_airport(airport_code: str) -> str:
    """
    Normalize ICAO airport code to uppercase
    
    Args:
        airport_code: ICAO airport code
        
    Returns:
        Normalized airport code
        
    Raises:
        ValueError: If airport code format is invalid
    """
    if not airport_code:
        raise ValueError("Airport code cannot be empty")
    
    normalized = airport_code.upper().strip()
    if not validate_icao_airport(normalized):
        raise ValueError(f"Invalid ICAO airport code format: {airport_code}")
    
    return normalized


def create_bounding_box(center_lat: float, center_lon: float, 
                       radius_km: float) -> BoundingBox:
    """
    Create a bounding box around a center point
    
    Args:
        center_lat: Center latitude in degrees
        center_lon: Center longitude in degrees
        radius_km: Radius in kilometers
        
    Returns:
        BoundingBox object
    """
    # Approximate conversion (more accurate for small areas)
    lat_delta = radius_km / 111.32  # roughly 111.32 km per degree latitude
    lon_delta = radius_km / (111.32 * math.cos(math.radians(center_lat)))
    
    return BoundingBox(
        min_latitude=max(-90, center_lat - lat_delta),
        max_latitude=min(90, center_lat + lat_delta),
        min_longitude=max(-180, center_lon - lon_delta),
        max_longitude=min(180, center_lon + lon_delta)
    )


def create_bounding_box_from_coordinates(coordinates: List[Tuple[float, float]]) -> BoundingBox:
    """
    Create bounding box from list of coordinate pairs
    
    Args:
        coordinates: List of (latitude, longitude) tuples
        
    Returns:
        BoundingBox encompassing all coordinates
        
    Raises:
        ValueError: If coordinates list is empty
    """
    if not coordinates:
        raise ValueError("Coordinates list cannot be empty")
    
    latitudes = [coord[0] for coord in coordinates]
    longitudes = [coord[1] for coord in coordinates]
    
    return BoundingBox(
        min_latitude=min(latitudes),
        max_latitude=max(latitudes),
        min_longitude=min(longitudes),
        max_longitude=max(longitudes)
    )


def haversine_distance(lat1: float, lon1: float, 
                      lat2: float, lon2: float) -> float:
    """
    Calculate great circle distance between two points using Haversine formula
    
    Args:
        lat1, lon1: First point coordinates in degrees
        lat2, lon2: Second point coordinates in degrees
        
    Returns:
        Distance in kilometers
    """
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (math.sin(dlat/2)**2 + 
         math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2)
    c = 2 * math.asin(math.sqrt(a))
    
    return 6371 * c  # Earth radius in km


def bearing_between_points(lat1: float, lon1: float,
                          lat2: float, lon2: float) -> float:
    """
    Calculate bearing between two geographic points
    
    Args:
        lat1, lon1: Start point coordinates in degrees
        lat2, lon2: End point coordinates in degrees
        
    Returns:
        Bearing in degrees (0-360)
    """
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    dlon = lon2 - lon1
    
    y = math.sin(dlon) * math.cos(lat2)
    x = (math.cos(lat1) * math.sin(lat2) - 
         math.sin(lat1) * math.cos(lat2) * math.cos(dlon))
    
    bearing = math.atan2(y, x)
    bearing = math.degrees(bearing)
    
    return (bearing + 360) % 360


def filter_states_by_distance(states: List[StateVector], 
                             center_lat: float, center_lon: float,
                             max_distance_km: float) -> List[StateVector]:
    """
    Filter state vectors by distance from a center point
    
    Args:
        states: List of StateVector objects
        center_lat: Center latitude in degrees
        center_lon: Center longitude in degrees
        max_distance_km: Maximum distance in kilometers
        
    Returns:
        Filtered list of StateVector objects
    """
    filtered = []
    for state in states:
        if state.has_position:
            distance = haversine_distance(
                center_lat, center_lon,
                state.latitude, state.longitude
            )
            if distance <= max_distance_km:
                filtered.append(state)
    return filtered


def filter_states_by_altitude(states: List[StateVector],
                             min_altitude: Optional[float] = None,
                             max_altitude: Optional[float] = None) -> List[StateVector]:
    """
    Filter state vectors by altitude range
    
    Args:
        states: List of StateVector objects
        min_altitude: Minimum altitude in meters (optional)
        max_altitude: Maximum altitude in meters (optional)
        
    Returns:
        Filtered list of StateVector objects
    """
    filtered = []
    for state in states:
        if state.baro_altitude is not None:
            altitude = state.baro_altitude
            
            if min_altitude is not None and altitude < min_altitude:
                continue
            if max_altitude is not None and altitude > max_altitude:
                continue
                
            filtered.append(state)
    return filtered


def sort_states_by_distance(states: List[StateVector],
                           center_lat: float, center_lon: float) -> List[StateVector]:
    """
    Sort state vectors by distance from center point
    
    Args:
        states: List of StateVector objects
        center_lat: Center latitude in degrees
        center_lon: Center longitude in degrees
        
    Returns:
        Sorted list of StateVector objects (closest first)
    """
    def distance_key(state: StateVector) -> float:
        if not state.has_position:
            return float('inf')
        return haversine_distance(
            center_lat, center_lon,
            state.latitude, state.longitude
        )
    
    return sorted(states, key=distance_key)


def states_to_dataframe(states: List[StateVector]) -> pd.DataFrame:
    """
    Convert list of StateVector objects to pandas DataFrame
    
    Args:
        states: List of StateVector objects
        
    Returns:
        pandas DataFrame with state data
    """
    data = []
    for state in states:
        data.append({
            'icao24': state.icao24,
            'callsign': state.callsign,
            'origin_country': state.origin_country,
            'time_position': state.time_position,
            'last_contact': state.last_contact,
            'longitude': state.longitude,
            'latitude': state.latitude,
            'baro_altitude': state.baro_altitude,
            'on_ground': state.on_ground,
            'velocity': state.velocity,
            'true_track': state.true_track,
            'vertical_rate': state.vertical_rate,
            'geo_altitude': state.geo_altitude,
            'squawk': state.squawk,
            'spi': state.spi,
            'position_source': state.position_source
        })
    
    return pd.DataFrame(data)


def flights_to_dataframe(flights: List[FlightData]) -> pd.DataFrame:
    """
    Convert list of FlightData objects to pandas DataFrame
    
    Args:
        flights: List of FlightData objects
        
    Returns:
        pandas DataFrame with flight data
    """
    data = []
    for flight in flights:
        data.append({
            'icao24': flight.icao24,
            'callsign': flight.callsign,
            'first_seen': flight.first_seen,
            'last_seen': flight.last_seen,
            'est_departure_airport': flight.est_departure_airport,
            'est_arrival_airport': flight.est_arrival_airport,
            'flight_duration_seconds': flight.flight_duration_seconds,
            'departure_datetime': flight.departure_datetime,
            'arrival_datetime': flight.arrival_datetime
        })
    
    return pd.DataFrame(data)


def waypoints_to_dataframe(waypoints: List[Waypoint]) -> pd.DataFrame:
    """
    Convert list of Waypoint objects to pandas DataFrame
    
    Args:
        waypoints: List of Waypoint objects
        
    Returns:
        pandas DataFrame with waypoint data
    """
    data = []
    for waypoint in waypoints:
        data.append({
            'time': waypoint.time,
            'datetime': waypoint.datetime,
            'latitude': waypoint.latitude,
            'longitude': waypoint.longitude,
            'baro_altitude': waypoint.baro_altitude,
            'true_track': waypoint.true_track,
            'on_ground': waypoint.on_ground
        })
    
    return pd.DataFrame(data)


def calculate_track_statistics(waypoints: List[Waypoint]) -> Dict[str, Any]:
    """
    Calculate statistics for a flight track
    
    Args:
        waypoints: List of Waypoint objects
        
    Returns:
        Dictionary with track statistics
    """
    if not waypoints:
        return {}
    
    position_waypoints = [wp for wp in waypoints if wp.has_position]
    
    if not position_waypoints:
        return {'waypoint_count': len(waypoints), 'position_count': 0}
    
    # Basic statistics
    altitudes = [wp.baro_altitude for wp in position_waypoints 
                if wp.baro_altitude is not None]
    tracks = [wp.true_track for wp in position_waypoints 
             if wp.true_track is not None]
    
    # Calculate total distance
    total_distance = 0.0
    for i in range(1, len(position_waypoints)):
        prev_wp = position_waypoints[i-1]
        curr_wp = position_waypoints[i]
        distance = haversine_distance(
            prev_wp.latitude, prev_wp.longitude,
            curr_wp.latitude, curr_wp.longitude
        )
        total_distance += distance
    
    stats = {
        'waypoint_count': len(waypoints),
        'position_count': len(position_waypoints),
        'total_distance_km': total_distance,
        'duration_seconds': waypoints[-1].time - waypoints[0].time,
        'start_time': waypoints[0].time,
        'end_time': waypoints[-1].time
    }
    
    if altitudes:
        stats.update({
            'min_altitude': min(altitudes),
            'max_altitude': max(altitudes),
            'avg_altitude': sum(altitudes) / len(altitudes)
        })
    
    if tracks:
        stats.update({
            'avg_track': sum(tracks) / len(tracks)
        })
    
    if total_distance > 0 and stats['duration_seconds'] > 0:
        stats['avg_speed_kmh'] = (total_distance / stats['duration_seconds']) * 3.6
    
    return stats


def parse_opensky_raw_state(raw_state: List) -> StateVector:
    """
    Parse raw OpenSky state array into StateVector object
    
    Args:
        raw_state: Raw state array from OpenSky API
        
    Returns:
        StateVector object
    """
    return StateVector(
        icao24=raw_state[0] or "",
        callsign=raw_state[1],
        origin_country=raw_state[2],
        time_position=raw_state[3],
        last_contact=raw_state[4],
        longitude=raw_state[5],
        latitude=raw_state[6],
        baro_altitude=raw_state[7],
        on_ground=raw_state[8],
        velocity=raw_state[9],
        true_track=raw_state[10],
        vertical_rate=raw_state[11],
        sensors=raw_state[12],
        geo_altitude=raw_state[13],
        squawk=raw_state[14],
        spi=raw_state[15],
        position_source=raw_state[16]
    )


def parse_opensky_raw_waypoint(raw_waypoint: List) -> Waypoint:
    """
    Parse raw OpenSky waypoint array into Waypoint object
    
    Args:
        raw_waypoint: Raw waypoint array from OpenSky API
        
    Returns:
        Waypoint object
    """
    return Waypoint(
        time=raw_waypoint[0],
        latitude=raw_waypoint[1],
        longitude=raw_waypoint[2],
        baro_altitude=raw_waypoint[3],
        true_track=raw_waypoint[4],
        on_ground=raw_waypoint[5]
    )