# API package for weather system
from .enhanced_weather_manager import EnhancedWeatherManager, WeatherData

# Backwards-compatible alias: keep old imports working
WeatherAPIManager = EnhancedWeatherManager