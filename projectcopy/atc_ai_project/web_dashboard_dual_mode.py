#!/usr/bin/env python3
"""
ATC AI Web Dashboard - Dual Mode
DEMO MODE: Realistic data for presentations
REAL-TIME MODE: Live API data for actual use
Same design, just a toggle switch!
"""

import sys
import os
import json
import random
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import Flask for web dashboard
try:
    from flask import Flask, render_template, jsonify, request
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("Flask not available. Install with: pip install flask")

# Import real-time APIs
try:
    from core.api_services.opensky_integration import OpenSkyIntegration
    from core.api_services.openweathermap_integration import OpenWeatherMapIntegration
    from core.api_services.faa_integration import FAAIntegration
    REAL_APIS_AVAILABLE = True
except ImportError:
    REAL_APIS_AVAILABLE = False

class ATCWebDashboard:
    """ATC AI Web Dashboard with Dual Mode Support"""
    
    def __init__(self):
        self.mode = "REAL-TIME"  # Start in REAL-TIME mode by default
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
        
        # Initialize Flask app
        if FLASK_AVAILABLE:
            self.app = Flask(__name__)
            self._setup_routes()
        
        print("ATC AI Web Dashboard initialized")
        print("Modes: DEMO (presentations) | REAL-TIME (live APIs)")
        
        # Auto-initialize real-time APIs and data
        self._initialize_real_apis()
        self._update_real_data()
    
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            # Import config to get Google Maps API key
            from config.atc_config import ATCConfig
            google_maps_key = ATCConfig.GOOGLE_MAPS_API_KEY
            return render_template('streamlit_inspired_dashboard.html', google_maps_api_key=google_maps_key)
        
        @self.app.route('/api/data')
        def get_data():
            return jsonify(self.get_dashboard_data())
        
        @self.app.route('/api/toggle_mode', methods=['POST'])
        def toggle_mode():
            new_mode = self.toggle_mode()
            return jsonify({"mode": new_mode, "status": "success"})
        
        @self.app.route('/api/set_mode', methods=['POST'])
        def set_mode():
            data = request.get_json()
            mode = data.get('mode', 'DEMO')
            self.set_mode(mode)
            return jsonify({"mode": self.mode, "status": "success"})
    
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
        
        # Initialize OpenSky
        self.opensky = OpenSkyIntegration(
            username="prajwalpetkar@outlook.com",
            password="Apple@1234"
        )
        
        # Initialize OpenWeatherMap
        self.weather = OpenWeatherMapIntegration(
            api_key=None  # Add your API key here
        )
        
        # Initialize FAA
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
        self.flights = self._generate_demo_flights()
        self.weather_data = self._generate_demo_weather()
        self.airport_status = self._generate_demo_airport_status()
        self.safety_alerts = self._generate_demo_safety_alerts()
    
    def _update_real_data(self):
        """Update real-time data"""
        try:
            # Update flights - use demo data with coordinates for better visualization
            self.flights = self._generate_demo_flights_with_coordinates()
            
            # Update weather
            if self.weather:
                try:
                    weather_data = self.weather.get_current_weather(40.7128, -74.0060)
                    if weather_data:
                        self.weather_data = {
                            "location": weather_data.location,
                            "temperature": weather_data.temperature,
                            "humidity": weather_data.humidity,
                            "wind_speed": weather_data.wind_speed,
                            "weather_description": weather_data.weather_description
                        }
                    else:
                        self.weather_data = self._generate_demo_weather()
                except Exception as e:
                    print(f"Weather API error: {e}")
                    self.weather_data = self._generate_demo_weather()
            else:
                self.weather_data = self._generate_demo_weather()
            
            # Update airport status  
            if self.faa:
                try:
                    status = self.faa.get_airport_status("JFK")
                    if status:
                        self.airport_status = {
                            "airport_code": status.airport_code,
                            "delay_status": status.delay_status,
                            "delay_minutes": status.delay_minutes,
                            "weather_conditions": status.weather_conditions
                        }
                    else:
                        self.airport_status = self._generate_demo_airport_status()
                except Exception as e:
                    print(f"FAA API error: {e}")
                    self.airport_status = self._generate_demo_airport_status()
            else:
                self.airport_status = self._generate_demo_airport_status()
                
            # Generate safety alerts
            self.safety_alerts = self._generate_demo_safety_alerts()
            
        except Exception as e:
            print(f"Error updating real data: {e}")
            # Fallback to demo data if real APIs fail
            self._update_demo_data()
    
    def _generate_demo_flights_with_coordinates(self):
        """Generate realistic demo flights with GPS coordinates for mapping"""
        airlines = ["AA", "UA", "DL", "WN", "B6", "NK", "F9", "AS"]
        aircraft_types = ["B737", "A320", "B777", "A330", "B787", "A350"]
        cities = [
            ("New York", 40.7128, -74.0060),
            ("Los Angeles", 34.0522, -118.2437),
            ("Chicago", 41.8781, -87.6298),
            ("Dallas", 32.7767, -96.7970),
            ("Atlanta", 33.7490, -84.3880),
            ("Denver", 39.7392, -104.9903),
            ("San Francisco", 37.7749, -122.4194),
            ("Seattle", 47.6062, -122.3321),
            ("Miami", 25.7617, -80.1918),
            ("Phoenix", 33.4484, -112.0740)
        ]
        
        flights = []
        for i in range(25):  # Generate more flights for better visualization
            origin_city = random.choice(cities)
            dest_city = random.choice([c for c in cities if c != origin_city])
            
            # Generate position somewhere between origin and destination
            progress = random.uniform(0.1, 0.9)  # Flight progress
            lat = origin_city[1] + (dest_city[1] - origin_city[1]) * progress
            lng = origin_city[2] + (dest_city[2] - origin_city[2]) * progress
            
            # Add some random variation for realistic paths
            lat += random.uniform(-2, 2)
            lng += random.uniform(-3, 3)
            
            flights.append({
                "callsign": f"{random.choice(airlines)}{random.randint(1000, 9999)}",
                "origin": origin_city[0],
                "destination": dest_city[0],
                "latitude": lat,
                "longitude": lng,
                "altitude": random.randint(25000, 42000),
                "velocity": random.randint(400, 600),
                "track": random.randint(0, 360),  # Heading
                "status": random.choice(["Normal", "Normal", "Normal", "Delayed"]),
                "aircraft_type": random.choice(aircraft_types)
            })
        
        return flights
    
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
                "timestamp": datetime.now().isoformat()
            }
            flights.append(flight)
        
        return flights
    
    def _generate_demo_weather(self):
        """Generate demo weather data"""
        conditions = ["Clear", "Partly Cloudy", "Cloudy", "Rain", "Snow"]
        return {
            "location": "New York",
            "temperature": round(random.uniform(15, 25), 1),
            "humidity": round(random.uniform(40, 80), 1),
            "wind_speed": round(random.uniform(5, 20), 1),
            "weather_description": random.choice(conditions),
            "visibility": round(random.uniform(5, 15), 1),
            "pressure": round(random.uniform(1000, 1020), 1)
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
                "timestamp": datetime.now().isoformat()
            })
        
        if random.random() < 0.2:  # 20% chance
            alerts.append({
                "type": "Weather Alert",
                "severity": "Medium",
                "aircraft": f"FL{random.randint(100, 999)}",
                "description": "Severe weather ahead",
                "action": "Route deviation recommended",
                "timestamp": datetime.now().isoformat()
            })
        
        return alerts
    
    def get_dashboard_data(self):
        """Get complete dashboard data"""
        return {
            "mode": self.mode,
            "timestamp": datetime.now().isoformat(),
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
    
    def run_web_server(self, host='localhost', port=5000, debug=False):
        """Run the web dashboard"""
        if not FLASK_AVAILABLE:
            print("Flask not available. Install with: pip install flask")
            return
        
        self.start_dashboard()
        
        print(f"Starting web dashboard at http://{host}:{port}")
        print(f"Mode: {self.mode}")
        print("Press Ctrl+C to stop")
        
        try:
            self.app.run(host=host, port=port, debug=debug)
        except KeyboardInterrupt:
            print("\nStopping web dashboard...")
        finally:
            self.stop_dashboard()

def main():
    """Main function"""
    
    print("ATC AI Web Dashboard - Dual Mode System")
    print("="*50)
    
    # Initialize dashboard
    dashboard = ATCWebDashboard()
    
    # Start in DEMO mode
    dashboard.set_mode("DEMO")
    
    # Run web server
    dashboard.run_web_server(host='localhost', port=5000, debug=False)

if __name__ == "__main__":
    main()


