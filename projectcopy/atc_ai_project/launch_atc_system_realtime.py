#!/usr/bin/env python3
"""
ATC AI System - Main Launcher with Real-Time APIs
Complete ATC AI system with live data integration
"""

import sys
import os
import time
import threading
from datetime import datetime
from typing import Dict, List, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import core systems
from core.safety_systems.collision_avoidance_engine import CollisionAvoidanceEngine
from core.safety_systems.conflict_zone_manager import ConflictZoneManager
from core.safety_systems.weather_avoidance_system import WeatherAvoidanceSystem
from core.api_services.unified_api_manager import UnifiedAPIManager, APIConfig

class ATCAISystem:
    """Main ATC AI System with Real-Time APIs"""
    
    def __init__(self):
        print("🚀 Initializing ATC AI System...")
        
        # Initialize safety systems
        self.collision_engine = CollisionAvoidanceEngine()
        self.conflict_manager = ConflictZoneManager()
        self.weather_system = WeatherAvoidanceSystem()
        
        # Initialize API manager
        self.api_manager = UnifiedAPIManager()
        
        # System status
        self.running = False
        self.update_thread = None
        
        print("✅ ATC AI System initialized successfully!")
    
    def configure_apis(self, opensky_username: str = None, opensky_password: str = None,
                      openweathermap_api_key: str = None):
        """Configure API credentials"""
        
        print("🔧 Configuring APIs...")
        
        # Configure OpenSky
        if opensky_username and opensky_password:
            self.api_manager.configure_api("opensky", APIConfig(
                service_name="OpenSky Network",
                enabled=True,
                username=opensky_username,
                password=opensky_password,
                rate_limit_delay=6.0
            ))
            print("✅ OpenSky Network configured")
        else:
            print("⚠️  OpenSky credentials not provided - using limited data")
        
        # Configure OpenWeatherMap
        if openweathermap_api_key:
            self.api_manager.configure_api("openweathermap", APIConfig(
                service_name="OpenWeatherMap",
                enabled=True,
                api_key=openweathermap_api_key,
                rate_limit_delay=1.0
            ))
            print("✅ OpenWeatherMap configured")
        else:
            print("⚠️  OpenWeatherMap API key not provided - using mock data")
        
        # Configure FAA (no credentials needed)
        self.api_manager.configure_api("faa", APIConfig(
            service_name="FAA Airport Status",
            enabled=True,
            rate_limit_delay=1.0
        ))
        print("✅ FAA Airport Status configured")
    
    def start_system(self):
        """Start the ATC AI system"""
        
        print("🚀 Starting ATC AI System...")
        
        # Initialize APIs
        self.api_manager.initialize_apis()
        
        # Load conflict zones
        self.conflict_manager.load_conflict_zones()
        
        # Load weather data
        self.weather_system.load_weather_data()
        
        # Start background updates
        self.api_manager.start_background_updates(update_interval=60)
        
        # Start system monitoring
        self.running = True
        self.update_thread = threading.Thread(target=self._system_monitor, daemon=True)
        self.update_thread.start()
        
        print("✅ ATC AI System started successfully!")
        print("📊 Real-time data collection active")
        print("🛡️  Safety systems operational")
    
    def stop_system(self):
        """Stop the ATC AI system"""
        
        print("🛑 Stopping ATC AI System...")
        
        self.running = False
        self.api_manager.stop_background_updates()
        
        if self.update_thread:
            self.update_thread.join(timeout=5)
        
        print("✅ ATC AI System stopped")
    
    def _system_monitor(self):
        """System monitoring loop"""
        
        while self.running:
            try:
                # Get system status
                health = self.api_manager.get_system_health()
                overview = self.api_manager.get_system_overview()
                
                # Display status every 5 minutes
                if int(time.time()) % 300 == 0:
                    self._display_system_status(health, overview)
                
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ Error in system monitor: {e}")
                time.sleep(5)
    
    def _display_system_status(self, health, overview):
        """Display system status"""
        
        print("\n" + "="*60)
        print("📊 ATC AI SYSTEM STATUS")
        print("="*60)
        print(f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🏥 System Health: {health.system_health.upper()}")
        print(f"🔌 Active APIs: {health.active_apis}/{health.total_apis}")
        print(f"📈 Data Points: {health.data_points_collected}")
        print(f"✅ Success Rate: {(health.successful_requests/health.total_requests*100):.1f}%" if health.total_requests > 0 else "N/A")
        
        print("\n📊 DATA SUMMARY:")
        print(f"✈️  Flights Tracked: {overview['data_summary']['total_flights']}")
        print(f"🌤️  Weather Locations: {overview['data_summary']['weather_locations']}")
        print(f"🛬 Airports Monitored: {overview['data_summary']['airports_tracked']}")
        
        print("\n🔧 API STATUS:")
        for api_name, status in overview['apis'].items():
            status_icon = "✅" if status.get('status') == 'operational' else "❌"
            print(f"{status_icon} {api_name.title()}: {status.get('status', 'unknown')}")
        
        print("="*60)
    
    def get_flight_data(self, area: Dict[str, float] = None) -> List[Dict[str, Any]]:
        """Get flight data for specific area"""
        
        if area:
            flights = self.api_manager.get_flights_in_area(
                area['min_lat'], area['max_lat'],
                area['min_lon'], area['max_lon']
            )
        else:
            # Default to US airspace
            flights = self.api_manager.get_flights_in_area(
                25.0, 49.0, -125.0, -66.0
            )
        
        # Convert to our format
        flight_data = []
        for flight in flights:
            flight_data.append(self.api_manager.apis['opensky'].convert_to_aircraft_format(flight))
        
        return flight_data
    
    def get_weather_data(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get weather data for specific location"""
        
        weather = self.api_manager.get_weather_at_location(lat, lon)
        if weather:
            return {
                "location": weather.location,
                "temperature": weather.temperature,
                "humidity": weather.humidity,
                "wind_speed": weather.wind_speed,
                "wind_direction": weather.wind_direction,
                "weather_description": weather.weather_description,
                "visibility": weather.visibility,
                "pressure": weather.pressure,
                "timestamp": weather.timestamp
            }
        return {}
    
    def get_airport_status(self, airport_code: str) -> Dict[str, Any]:
        """Get airport status"""
        
        status = self.api_manager.get_airport_status(airport_code)
        if status:
            return {
                "airport_code": status.airport_code,
                "airport_name": status.airport_name,
                "delay_status": status.delay_status,
                "delay_minutes": status.delay_minutes,
                "delay_reason": status.delay_reason,
                "weather_conditions": status.weather_conditions,
                "visibility": status.visibility,
                "wind_speed": status.wind_speed,
                "temperature": status.temperature,
                "last_updated": status.last_updated
            }
        return {}
    
    def analyze_safety_risks(self, flight_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze safety risks using all systems"""
        
        print("🛡️  Analyzing safety risks...")
        
        # Convert to Aircraft objects for collision detection
        from core.safety_systems.collision_avoidance_engine import Aircraft
        
        aircraft_list = []
        for flight in flight_data:
            aircraft = Aircraft(
                icao24=flight['icao24'],
                callsign=flight['callsign'],
                latitude=flight['latitude'],
                longitude=flight['longitude'],
                altitude=flight['altitude'],
                velocity=flight['velocity'],
                heading=flight['heading'],
                vertical_rate=flight['vertical_rate'],
                timestamp=flight['timestamp']
            )
            aircraft_list.append(aircraft)
        
        # Detect collisions
        conflicts = self.collision_engine.detect_conflicts(aircraft_list)
        
        # Check conflict zones
        conflict_zone_risks = []
        for aircraft in aircraft_list:
            zones = self.conflict_manager.check_aircraft_in_conflict_zone(
                aircraft.latitude, aircraft.longitude, aircraft.altitude
            )
            if zones:
                conflict_zone_risks.append({
                    "aircraft": aircraft.icao24,
                    "conflicting_zones": [zone.zone_id for zone in zones]
                })
        
        # Analyze weather risks
        weather_risks = []
        for aircraft in aircraft_list:
            hazards = self.weather_system.assess_weather_impact(
                [(aircraft.latitude, aircraft.longitude)],
                [aircraft.altitude]
            )
            if hazards:
                weather_risks.append({
                    "aircraft": aircraft.icao24,
                    "hazards": [hazard.hazard_type for hazard in hazards]
                })
        
        return {
            "collision_conflicts": len(conflicts),
            "conflict_details": [
                {
                    "aircraft1": conflict.aircraft1,
                    "aircraft2": conflict.aircraft2,
                    "severity": conflict.severity,
                    "time_to_conflict": conflict.time_to_conflict,
                    "recommended_action": conflict.recommended_action
                } for conflict in conflicts
            ],
            "conflict_zone_risks": conflict_zone_risks,
            "weather_risks": weather_risks,
            "total_risks": len(conflicts) + len(conflict_zone_risks) + len(weather_risks),
            "analysis_timestamp": datetime.now()
        }
    
    def get_system_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        
        # Get all data
        flight_data = self.get_flight_data()
        weather_data = self.get_weather_data(40.7128, -74.0060)  # New York
        airport_status = self.get_airport_status("JFK")
        safety_analysis = self.analyze_safety_risks(flight_data)
        system_health = self.api_manager.get_system_health()
        
        return {
            "timestamp": datetime.now(),
            "system_health": {
                "status": system_health.system_health,
                "active_apis": system_health.active_apis,
                "total_apis": system_health.total_apis,
                "data_points": system_health.data_points_collected
            },
            "flight_data": {
                "total_flights": len(flight_data),
                "flights": flight_data[:10]  # First 10 flights
            },
            "weather_data": weather_data,
            "airport_status": airport_status,
            "safety_analysis": safety_analysis,
            "conflict_zones": {
                "total_zones": len(self.conflict_manager.conflict_zones),
                "active_zones": len(self.conflict_manager.get_active_zones())
            },
            "weather_conditions": {
                "total_conditions": len(self.weather_system.weather_conditions),
                "active_conditions": len([c for c in self.weather_system.weather_conditions.values() 
                                       if not c.end_time or c.end_time > datetime.now()])
            }
        }

def main():
    """Main function to run the ATC AI system"""
    
    print("🚀 ATC AI SYSTEM - REAL-TIME VERSION")
    print("="*50)
    
    # Initialize system
    atc_system = ATCAISystem()
    
    # Configure APIs (you can add your credentials here)
    print("\n🔧 API Configuration:")
    print("To get FREE API access:")
    print("1. OpenSky: https://opensky-network.org/ (Register for FREE)")
    print("2. OpenWeatherMap: https://openweathermap.org/api (Register for FREE)")
    print("3. FAA: No registration needed (Public API)")
    
    # Ask for credentials
    opensky_username = input("\nEnter OpenSky username (or press Enter to skip): ").strip()
    opensky_password = input("Enter OpenSky password (or press Enter to skip): ").strip()
    openweathermap_api_key = input("Enter OpenWeatherMap API key (or press Enter to skip): ").strip()
    
    # Configure APIs
    atc_system.configure_apis(
        opensky_username=opensky_username if opensky_username else None,
        opensky_password=opensky_password if opensky_password else None,
        openweathermap_api_key=openweathermap_api_key if openweathermap_api_key else None
    )
    
    # Start system
    atc_system.start_system()
    
    try:
        print("\n🎯 ATC AI System is running!")
        print("Press Ctrl+C to stop...")
        
        # Keep running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping system...")
        atc_system.stop_system()
        print("✅ System stopped successfully!")

if __name__ == "__main__":
    main()


