"""
ATC Project Configuration
Centralized configuration for all API keys and settings
"""

import os
from typing import Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ATCConfig:
    """Configuration management for ATC AI Project"""
    
    # Google Maps API Configuration (Primary for ATC project)
    GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')  # No default - set via environment
    
    # OpenSky Network Configuration
    OPENSKY_CLIENT_ID = os.getenv('OPENSKY_CLIENT_ID', 'ramprasadsharma.engineer-api-client')
    OPENSKY_CLIENT_SECRET = os.getenv('OPENSKY_CLIENT_SECRET')  # No default - set via environment
    OPENSKY_BASE_URL = os.getenv('OPENSKY_BASE_URL', 'https://opensky-network.org/api')
    
    # OpenWeatherMap Configuration
    OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')  # No default - set via environment
    OPENWEATHER_BASE_URL = os.getenv('OPENWEATHER_BASE_URL', 'http://api.openweathermap.org/data/2.5')
    
    # AviationStack Configuration
    AVIATIONSTACK_API_KEY = os.getenv('AVIATIONSTACK_API_KEY')  # No default - set via environment
    AVIATIONSTACK_BASE_URL = os.getenv('AVIATIONSTACK_BASE_URL', 'http://api.aviationstack.com/v1')
    
    # System Configuration
    DEFAULT_UPDATE_INTERVAL = 30  # seconds
    DEFAULT_MAP_CENTER = [39.8283, -98.5795]  # Center of USA
    DEFAULT_MAP_ZOOM = 4
    
    # Dashboard Configuration
    STREAMLIT_PORT = 8501
    FLASK_PORT = 5000
    
    @classmethod
    def get_google_maps_config(cls) -> Dict:
        """Get Google Maps configuration"""
        return {
            'api_key': cls.GOOGLE_MAPS_API_KEY,
            'geocoding_enabled': True,
            'static_maps_enabled': True,
            'directions_enabled': True,
            'places_enabled': True
        }
    
    @classmethod
    def get_opensky_config(cls) -> Dict:
        """Get OpenSky Network configuration"""
        return {
            'client_id': cls.OPENSKY_CLIENT_ID,
            'client_secret': cls.OPENSKY_CLIENT_SECRET,
            'base_url': cls.OPENSKY_BASE_URL,
            'authenticated': bool(cls.OPENSKY_CLIENT_ID and cls.OPENSKY_CLIENT_SECRET)
        }
    
    @classmethod
    def get_weather_config(cls) -> Dict:
        """Get weather API configuration"""
        return {
            'openweather_key': cls.OPENWEATHER_API_KEY,
            'openweather_url': cls.OPENWEATHER_BASE_URL,
            'enabled': bool(cls.OPENWEATHER_API_KEY)
        }
    
    @classmethod
    def get_all_config(cls) -> Dict:
        """Get complete configuration status"""
        return {
            'google_maps': cls.get_google_maps_config(),
            'opensky': cls.get_opensky_config(),
            'weather': cls.get_weather_config(),
            'system': {
                'update_interval': cls.DEFAULT_UPDATE_INTERVAL,
                'map_center': cls.DEFAULT_MAP_CENTER,
                'map_zoom': cls.DEFAULT_MAP_ZOOM,
                'streamlit_port': cls.STREAMLIT_PORT
            }
        }
    
    @classmethod
    def validate_config(cls) -> Dict:
        """Validate all API configurations"""
        status = {
            'google_maps': cls.GOOGLE_MAPS_API_KEY is not None,
            'opensky': cls.OPENSKY_CLIENT_ID is not None and cls.OPENSKY_CLIENT_SECRET is not None,
            'weather': cls.OPENWEATHER_API_KEY is not None,
            'aviation': cls.AVIATIONSTACK_API_KEY is not None
        }
        
        status['all_configured'] = all(status.values())
        status['essential_configured'] = status['google_maps'] and status['opensky']
        
        return status


# Create global config instance
config = ATCConfig()

# Export commonly used configurations
GOOGLE_MAPS_API_KEY = config.GOOGLE_MAPS_API_KEY
OPENSKY_CONFIG = config.get_opensky_config()
WEATHER_CONFIG = config.get_weather_config()

if __name__ == "__main__":
    # Test configuration
    print("🛩️  ATC Project Configuration Status")
    print("=" * 40)
    
    # Validate all configurations
    validation = ATCConfig.validate_config()
    
    print("API Configuration Status:")
    print(f"✅ Google Maps API: {'Configured' if validation['google_maps'] else 'Missing'}")
    print(f"✅ OpenSky Network: {'Configured' if validation['opensky'] else 'Missing'}")
    print(f"✅ Weather API: {'Configured' if validation['weather'] else 'Missing'}")
    print(f"✅ Aviation Stack: {'Configured' if validation['aviation'] else 'Missing'}")
    
    print(f"\n🎯 Overall Status:")
    print(f"Essential APIs: {'✅ Ready' if validation['essential_configured'] else '❌ Missing'}")
    print(f"All APIs: {'✅ Complete' if validation['all_configured'] else '⚠️ Partial'}")
    
    print(f"\n🗺️  Google Maps Configuration:")
    google_config = ATCConfig.get_google_maps_config()
    print(f"API Key: {google_config['api_key'][:20]}...")
    print(f"Geocoding: {'✅ Enabled' if google_config['geocoding_enabled'] else '❌ Disabled'}")
    print(f"Static Maps: {'✅ Enabled' if google_config['static_maps_enabled'] else '❌ Disabled'}")
    print(f"Directions: {'✅ Enabled' if google_config['directions_enabled'] else '❌ Disabled'}")
    
    print(f"\n🛰️  OpenSky Configuration:")
    opensky_config = ATCConfig.get_opensky_config()
    print(f"Client ID: {opensky_config['client_id']}")
    print(f"Authenticated: {'✅ Yes' if opensky_config['authenticated'] else '❌ No'}")
    
    print(f"\n🌤️  Weather Configuration:")
    weather_config = ATCConfig.get_weather_config()
    print(f"API Key: {weather_config['openweather_key'][:20] if weather_config['openweather_key'] else 'Not set'}...")
    print(f"Enabled: {'✅ Yes' if weather_config['enabled'] else '❌ No'}")
    
    print("\n🚀 Your ATC project is ready to launch!")