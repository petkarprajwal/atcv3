"""
Models module for OpenSky API integration
"""

from .opensky_models import (
    BoundingBox,
    StateVector,
    OpenSkyStates,
    Waypoint,
    FlightTrack,
    FlightData,
    APIError,
    APIResponse
)

__all__ = [
    'BoundingBox',
    'StateVector', 
    'OpenSkyStates',
    'Waypoint',
    'FlightTrack',
    'FlightData',
    'APIError',
    'APIResponse'
]