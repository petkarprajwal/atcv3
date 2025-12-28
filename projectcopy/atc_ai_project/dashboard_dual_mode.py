#!/usr/bin/env python3
"""
ATC AI Dashboard - Dual Mode System
DEMO MODE: Realistic data for presentations
REAL-TIME MODE: Live API data for actual use
"""

import sys
import os
import random
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import real-time APIs
try:
    from core.api_services.opensky_integration import OpenSkyIntegration
    from core.api_services.openweathermap_integration import OpenWeatherMapIntegration
    from core.api_services.faa_integration import FAAIntegration
    REAL_APIS_AVAILABLE = True
except ImportError:
    REAL_APIS_AVAILABLE = False

class ATCDashboard:
    """ATC AI Dashboard with Dual Mode Support"""
    
    def __init__(self):
        self.mode = "DEMO"  # "DEMO" or "REAL-TIME"
        self.running = False
        self.update_thread = None
        
        # Real-time API instances
        self.opensky = None
        self.weather = None
        self.faa = None
        
        # Data storage
        self.flights = []
        self.weather_data = {}
        self.airport_status = {}
        self.safety_alerts = []
        
        print("ATC AI Dashboard initialized")
        print("Modes available: DEMO (for presentations) | REAL-TIME (live APIs)")
    
    def set_mode(self, mode: str):
        """Set dashboard mode"""
        if mode.upper() in ["DEMO", "REAL-TIME"]:
            self.mode = mode.upper()
            print(f"Dashboard mode set to: {self.mode}")
            
            if self.mode == "REAL-TIME":
                self._initialize_real_apis()
            else:
                self._stop_real_apis()
        else:
            print("Invalid mode. Use 'DEMO' or 'REAL-TIME'")
    
    def _initialize_real_apis(self):
        """Initialize real-time APIs"""
        if not REAL_APIS_AVAILABLE:
            print("Real-time APIs not available. Switching to DEMO mode.")
            self.mode = "DEMO"
            return
        
        print("Initializing real-time APIs...")
        
        # Initialize OpenSky (you can add credentials here)
        self.opensky = OpenSkyIntegration(
            username="prajwalpetkar@outlook.com",
            password="Apple@1234"
        )
        
        # Initialize OpenWeatherMap (add your API key here)
        self.weather = OpenWeatherMapIntegration(
            api_key=None  # Add your API key here
        )
        
        # Initialize FAA (no credentials needed)
        self.faa = FAAIntegration()
        
        print("Real-time APIs initialized")
    
    def _stop_real_apis(self):
        """Stop real-time APIs"""
        self.opensky = None
        self.weather = None
        self.faa = None
        print("Real-time APIs stopped")
    
    def start_dashboard(self):
        """Start the dashboard"""
        self.running = True
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
        print(f"Dashboard started in {self.mode} mode")
    
    def stop_dashboard(self):
        """Stop the dashboard"""
        self.running = False
        if self.update_thread:
            self.update_thread.join(timeout=5)
        print("Dashboard stopped")
    
    def _update_loop(self):
        """Main update loop"""
        while self.running:
            try:
                if self.mode == "DEMO":
                    self._update_demo_data()
                else:
                    self._update_real_data()
                
                time.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                print(f"Error in update loop: {e}")
                time.sleep(10)
    
    def _update_demo_data(self):
        """Update demo data"""
        # Generate realistic flight data
        self.flights = self._generate_demo_flights()
        
        # Generate weather data
        self.weather_data = self._generate_demo_weather()
        
        # Generate airport status
        self.airport_status = self._generate_demo_airport_status()
        
        # Generate safety alerts
        self.safety_alerts = self._generate_demo_safety_alerts()
    
    def _update_real_data(self):
        """Update real-time data"""
        try:
            # Update flights
            if self.opensky:
                real_flights = self.opensky.get_flights_by_area(
                    25.0, 49.0, -125.0, -66.0  # US airspace
                )
                self.flights = [self.opensky.convert_to_aircraft_format(f) for f in real_flights]
            
            # Update weather
            if self.weather:
                weather_data = self.weather.get_current_weather(40.7128, -74.0060)
                if weather_data:
                    self.weather_data = {
                        "location": weather_data.location,
                        "temperature": weather_data.temperature,
                        "humidity": weather_data.humidity,
                        "wind_speed": weather_data.wind_speed,
                        "weather_description": weather_data.weather_description
                    }
            
            # Update airport status
            if self.faa:
                status = self.faa.get_airport_status("JFK")
                if status:
                    self.airport_status = {
                        "airport_code": status.airport_code,
                        "delay_status": status.delay_status,
                        "delay_minutes": status.delay_minutes,
                        "weather_conditions": status.weather_conditions
                    }
            
        except Exception as e:
            print(f"Error updating real data: {e}")
            # Fallback to demo data if real APIs fail
            self._update_demo_data()
    
    def _generate_demo_flights(self):
        """Generate realistic demo flights"""
        airlines = ["AA", "UA", "DL", "WN", "B6", "NK", "F9", "AS"]
        aircraft_types = ["B737", "A320", "B777", "A330", "B787", "A350"]
        cities = [
            ("New York", 40.7128, -74.0060),
            ("Los Angeles", 34.0522, -118.2437),
            ("Chicago", 41.8781, -87.6298),
            ("Dallas", 32.7767, -96.7970),
            ("Atlanta", 33.7490, -84.3880),
            ("Denver", 39.7392, -104.9903)
        ]
        
        flights = []
        num_flights = random.randint(20, 35)
        
        for i in range(num_flights):
            origin = random.choice(cities)
            destination = random.choice([city for city in cities if city != origin])
            
            progress = random.uniform(0.1, 0.9)
            lat = origin[1] + (destination[1] - origin[1]) * progress + random.uniform(-1, 1)
            lon = origin[2] + (destination[2] - origin[2]) * progress + random.uniform(-1, 1)
            
            flight = {
                "callsign": f"{random.choice(airlines)}{random.randint(100, 9999)}",
                "icao24": f"ABC{random.randint(100, 999)}",
                "aircraft_type": random.choice(aircraft_types),
                "origin": origin[0],
                "destination": destination[0],
                "latitude": round(lat, 4),
                "longitude": round(lon, 4),
                "altitude": random.randint(25000, 45000),
                "velocity": random.randint(400, 600),
                "heading": random.randint(0, 360),
                "vertical_rate": random.randint(-2000, 2000),
                "timestamp": datetime.now()
            }
            flights.append(flight)
        
        return flights
    
    def _generate_demo_weather(self):
        """Generate demo weather data"""
        conditions = ["Clear", "Partly Cloudy", "Cloudy", "Rain", "Snow"]
        return {
            "location": "New York",
            "temperature": random.uniform(15, 25),
            "humidity": random.uniform(40, 80),
            "wind_speed": random.uniform(5, 20),
            "weather_description": random.choice(conditions),
            "visibility": random.uniform(5, 15),
            "pressure": random.uniform(1000, 1020)
        }
    
    def _generate_demo_airport_status(self):
        """Generate demo airport status"""
        airports = ["JFK", "LAX", "ORD", "DFW", "ATL"]
        statuses = ["Normal", "Minor Delays", "Moderate Delays", "Major Delays"]
        
        airport = random.choice(airports)
        status = random.choice(statuses)
        
        return {
            "airport_code": airport,
            "delay_status": status,
            "delay_minutes": random.randint(0, 60) if status != "Normal" else 0,
            "weather_conditions": random.choice(["Clear", "Rain", "Snow", "Fog"]),
            "runway_status": "Operational"
        }
    
    def _generate_demo_safety_alerts(self):
        """Generate demo safety alerts"""
        alerts = []
        
        # Randomly generate alerts
        if random.random() < 0.3:  # 30% chance
            alerts.append({
                "type": "Collision Risk",
                "severity": "High",
                "aircraft": f"FL{random.randint(100, 999)}",
                "description": "Potential collision detected",
                "action": "Immediate altitude change required",
                "timestamp": datetime.now()
            })
        
        if random.random() < 0.2:  # 20% chance
            alerts.append({
                "type": "Weather Alert",
                "severity": "Medium",
                "aircraft": f"FL{random.randint(100, 999)}",
                "description": "Severe weather ahead",
                "action": "Route deviation recommended",
                "timestamp": datetime.now()
            })
        
        return alerts
    
    def get_dashboard_data(self):
        """Get complete dashboard data"""
        return {
            "mode": self.mode,
            "timestamp": datetime.now(),
            "flights": {
                "total": len(self.flights),
                "data": self.flights[:10]  # First 10 flights
            },
            "weather": self.weather_data,
            "airports": self.airport_status,
            "safety_alerts": self.safety_alerts,
            "system_status": {
                "status": "operational",
                "mode": self.mode,
                "last_update": datetime.now().strftime("%H:%M:%S")
            }
        }
    
    def toggle_mode(self):
        """Toggle between DEMO and REAL-TIME modes"""
        if self.mode == "DEMO":
            self.set_mode("REAL-TIME")
        else:
            self.set_mode("DEMO")
        return self.mode

def main():
    """Main dashboard function"""
    
    print("ATC AI Dashboard - Dual Mode System")
    print("="*50)
    
    # Initialize dashboard
    dashboard = ATCDashboard()
    
    # Start in DEMO mode
    dashboard.set_mode("DEMO")
    dashboard.start_dashboard()
    
    try:
        print("\nDashboard is running!")
        print("Commands:")
        print("  'toggle' - Switch between DEMO and REAL-TIME modes")
        print("  'status' - Show current status")
        print("  'quit' - Exit dashboard")
        print()
        
        while True:
            command = input("Dashboard> ").strip().lower()
            
            if command == "toggle":
                new_mode = dashboard.toggle_mode()
                print(f"Switched to {new_mode} mode")
                
            elif command == "status":
                data = dashboard.get_dashboard_data()
                print(f"\nMode: {data['mode']}")
                print(f"Flights: {data['flights']['total']}")
                print(f"Weather: {data['weather']['weather_description']}")
                print(f"Airport: {data['airports']['airport_code']} - {data['airports']['delay_status']}")
                print(f"Safety Alerts: {len(data['safety_alerts'])}")
                print(f"Last Update: {data['system_status']['last_update']}")
                
            elif command == "quit":
                break
                
            else:
                print("Unknown command. Use 'toggle', 'status', or 'quit'")
    
    except KeyboardInterrupt:
        print("\nStopping dashboard...")
    
    finally:
        dashboard.stop_dashboard()
        print("Dashboard stopped.")

if __name__ == "__main__":
    main()


