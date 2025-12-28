"""
Google Maps Integration for ATC AI System
Provides enhanced mapping capabilities with Google Maps API
"""

import os
import requests
import json
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class GoogleMapsIntegration:
    """Google Maps API integration for ATC system"""
    
    def __init__(self):
        """Initialize Google Maps integration"""
        # Primary API key for ATC project (updated key with billing enabled)
        self.primary_api_key = "AIzaSyCXMuWvccDLIA4PFfjcxgvloZcQrPDDfL4"
        
        # Also check environment variables as backup
        self.geo_api_key = os.getenv('GOOGLE_GEO_MAP_KEY')
        self.map_api_key = os.getenv('GOOGLE_MAP_KEY')
        
        # Use the specified primary key, fallback to environment
        self.api_key = self.primary_api_key or self.geo_api_key or self.map_api_key
        
        if not self.api_key:
            logger.warning("No Google Maps API key found in environment variables")
        
        self.base_url = "https://maps.googleapis.com/maps/api"
        
    def geocode_airport(self, airport_code: str) -> Optional[Dict]:
        """
        Get coordinates for an airport using its ICAO/IATA code
        
        Args:
            airport_code: ICAO or IATA airport code (e.g., 'KJFK', 'JFK')
            
        Returns:
            Dictionary with lat, lng, formatted_address, or None if not found
        """
        if not self.api_key:
            return None
            
        try:
            # Search for airport by code
            query = f"{airport_code} airport"
            url = f"{self.base_url}/geocode/json"
            
            params = {
                'address': query,
                'key': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] == 'OK' and data['results']:
                result = data['results'][0]
                location = result['geometry']['location']
                
                return {
                    'lat': location['lat'],
                    'lng': location['lng'],
                    'formatted_address': result['formatted_address'],
                    'place_id': result.get('place_id'),
                    'airport_code': airport_code
                }
            else:
                logger.warning(f"No results found for airport: {airport_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error geocoding airport {airport_code}: {e}")
            return None
        except (KeyError, IndexError) as e:
            logger.error(f"Error parsing geocoding response for {airport_code}: {e}")
            return None
    
    def reverse_geocode(self, lat: float, lng: float) -> Optional[Dict]:
        """
        Get address information from coordinates
        
        Args:
            lat: Latitude
            lng: Longitude
            
        Returns:
            Dictionary with address components or None if not found
        """
        if not self.api_key:
            return None
            
        try:
            url = f"{self.base_url}/geocode/json"
            
            params = {
                'latlng': f"{lat},{lng}",
                'key': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] == 'OK' and data['results']:
                result = data['results'][0]
                
                return {
                    'formatted_address': result['formatted_address'],
                    'address_components': result['address_components'],
                    'place_id': result.get('place_id')
                }
            else:
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error reverse geocoding {lat},{lng}: {e}")
            return None
    
    def get_flight_path_waypoints(self, origin: str, destination: str, 
                                waypoints: List[str] = None) -> Optional[Dict]:
        """
        Get optimized flight path between airports with optional waypoints
        
        Args:
            origin: Origin airport code
            destination: Destination airport code
            waypoints: List of waypoint airport codes
            
        Returns:
            Dictionary with route information
        """
        if not self.api_key:
            return None
            
        try:
            # Get coordinates for origin and destination
            origin_coords = self.geocode_airport(origin)
            dest_coords = self.geocode_airport(destination)
            
            if not origin_coords or not dest_coords:
                return None
            
            # Build waypoints string if provided
            waypoints_str = ""
            if waypoints:
                waypoint_coords = []
                for wp in waypoints:
                    wp_coords = self.geocode_airport(wp)
                    if wp_coords:
                        waypoint_coords.append(f"{wp_coords['lat']},{wp_coords['lng']}")
                
                if waypoint_coords:
                    waypoints_str = "|".join(waypoint_coords)
            
            # Get directions
            url = f"{self.base_url}/directions/json"
            
            params = {
                'origin': f"{origin_coords['lat']},{origin_coords['lng']}",
                'destination': f"{dest_coords['lat']},{dest_coords['lng']}",
                'key': self.api_key,
                'mode': 'driving',  # Using driving as closest approximation to flight path
                'avoid': 'tolls',
                'units': 'metric'
            }
            
            if waypoints_str:
                params['waypoints'] = waypoints_str
            
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] == 'OK' and data['routes']:
                route = data['routes'][0]
                
                # Extract path coordinates
                path_coords = []
                for leg in route['legs']:
                    for step in leg['steps']:
                        path_coords.append([
                            step['start_location']['lat'],
                            step['start_location']['lng']
                        ])
                        path_coords.append([
                            step['end_location']['lat'],
                            step['end_location']['lng']
                        ])
                
                return {
                    'origin': origin_coords,
                    'destination': dest_coords,
                    'path_coordinates': path_coords,
                    'distance': route['legs'][0]['distance']['text'],
                    'duration': route['legs'][0]['duration']['text'],
                    'overview_polyline': route['overview_polyline']['points']
                }
            else:
                logger.warning(f"No route found from {origin} to {destination}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting flight path from {origin} to {destination}: {e}")
            return None
        except (KeyError, IndexError) as e:
            logger.error(f"Error parsing directions response: {e}")
            return None
    
    def get_static_map_url(self, center_lat: float, center_lng: float, 
                          zoom: int = 10, size: str = "800x600",
                          markers: List[Dict] = None) -> Optional[str]:
        """
        Generate static map URL with markers
        
        Args:
            center_lat: Center latitude
            center_lng: Center longitude
            zoom: Zoom level (1-20)
            size: Map size (e.g., "800x600")
            markers: List of marker dictionaries with lat, lng, label
            
        Returns:
            Static map URL or None if no API key
        """
        if not self.api_key:
            return None
        
        url = f"{self.base_url}/staticmap"
        
        params = {
            'center': f"{center_lat},{center_lng}",
            'zoom': zoom,
            'size': size,
            'maptype': 'roadmap',
            'key': self.api_key
        }
        
        # Add markers if provided
        if markers:
            marker_strings = []
            for marker in markers:
                marker_str = f"color:red|label:{marker.get('label', 'A')}|{marker['lat']},{marker['lng']}"
                marker_strings.append(marker_str)
            
            params['markers'] = marker_strings
        
        # Build URL with parameters
        param_str = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{url}?{param_str}"
    
    def get_nearby_airports(self, lat: float, lng: float, 
                           radius: int = 50000) -> List[Dict]:
        """
        Find airports near a given location
        
        Args:
            lat: Latitude
            lng: Longitude
            radius: Search radius in meters (default 50km)
            
        Returns:
            List of nearby airports
        """
        if not self.api_key:
            return []
        
        try:
            url = f"{self.base_url}/place/nearbysearch/json"
            
            params = {
                'location': f"{lat},{lng}",
                'radius': radius,
                'type': 'airport',
                'key': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            airports = []
            if data['status'] == 'OK':
                for place in data['results']:
                    airports.append({
                        'name': place['name'],
                        'lat': place['geometry']['location']['lat'],
                        'lng': place['geometry']['location']['lng'],
                        'place_id': place['place_id'],
                        'rating': place.get('rating'),
                        'vicinity': place.get('vicinity')
                    })
            
            return airports
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error finding nearby airports: {e}")
            return []
    
    def is_configured(self) -> bool:
        """Check if Google Maps API is properly configured"""
        return self.api_key is not None
    
    def get_api_status(self) -> Dict:
        """Get API configuration status"""
        return {
            'configured': self.is_configured(),
            'primary_key_active': self.api_key == self.primary_api_key,
            'geo_key_available': self.geo_api_key is not None,
            'map_key_available': self.map_api_key is not None,
            'active_key_source': 'primary' if self.api_key == self.primary_api_key else 'geo_env' if self.api_key == self.geo_api_key else 'map_env' if self.api_key == self.map_api_key else None,
            'key_preview': f"{self.api_key[:20]}..." if self.api_key else None
        }


# Usage example and testing
if __name__ == "__main__":
    # Test the Google Maps integration
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    maps = GoogleMapsIntegration()
    
    if maps.is_configured():
        print("✅ Google Maps API configured successfully")
        print(f"API Status: {maps.get_api_status()}")
        
        # Test airport geocoding
        print("\\n--- Testing Airport Geocoding ---")
        jfk = maps.geocode_airport("KJFK")
        if jfk:
            print(f"JFK Airport: {jfk['lat']}, {jfk['lng']}")
            print(f"Address: {jfk['formatted_address']}")
        
        # Test nearby airports
        print("\\n--- Testing Nearby Airports ---")
        if jfk:
            nearby = maps.get_nearby_airports(jfk['lat'], jfk['lng'])
            print(f"Found {len(nearby)} nearby airports")
            for airport in nearby[:3]:
                print(f"- {airport['name']}: {airport['lat']}, {airport['lng']}")
        
        # Test static map URL
        print("\\n--- Testing Static Map URL ---")
        if jfk:
            map_url = maps.get_static_map_url(
                jfk['lat'], jfk['lng'], 
                zoom=12, 
                markers=[{'lat': jfk['lat'], 'lng': jfk['lng'], 'label': 'JFK'}]
            )
            print(f"Static map URL: {map_url}")
    
    else:
        print("❌ Google Maps API not configured")
        print("Please add GOOGLE_GEO_MAP_KEY or GOOGLE_MAP_KEY to your .env file")