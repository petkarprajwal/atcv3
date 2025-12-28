"""
Weather Monitoring System for Enhanced Weather Integration
Real-time monitoring with hazard detection and alerting
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Callable, Any, Optional
from api import WeatherAPIManager, WeatherData

class WeatherMonitor:
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {'monitoring_interval': 60}
        self.weather_manager = None
        self.airports = ['JFK', 'LAX', 'ORD', 'ATL', 'DFW', 'DEN', 'LHR', 'CDG']
        self.alert_callbacks: List[Callable] = []
        self.running = False
    def add_alert_callback(self, callback: Callable):
        self.alert_callbacks.append(callback)
    async def start_monitoring(self):
        self.running = True
        self.weather_manager = WeatherAPIManager({'primary_source': 'openweathermap', 'api_key': self.config.get('api_key', None)})
        while self.running:
            async with self.weather_manager as wm:
                weather_data = await wm.get_batch_weather(self.airports)
                for airport, data in weather_data.items():
                    if data.conditions in ['storm', 'rain']:
                        for cb in self.alert_callbacks:
                            await cb({'airport': airport, 'condition': data.conditions, 'timestamp': data.timestamp})
            await asyncio.sleep(self.config['monitoring_interval'])
    async def stop_monitoring(self):
        self.running = False
