#!/usr/bin/env python3
"""
Weather Avoidance System
Advanced weather detection and avoidance system for ATC AI
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
import logging
import math
import json
import requests
from scipy.interpolate import griddata
from scipy.ndimage import gaussian_filter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class WeatherCondition:
    """Weather condition data structure"""
    condition_id: str
    condition_type: str  # "thunderstorm", "turbulence", "icing", "wind_shear", "volcanic_ash"
    severity: str  # "light", "moderate", "severe", "extreme"
    latitude: float
    longitude: float
    altitude_min: float
    altitude_max: float
    radius: float  # km
    intensity: float  # 0-1 scale
    movement_direction: float  # degrees
    movement_speed: float  # km/h
    start_time: datetime
    end_time: Optional[datetime]
    confidence: float  # 0-1 scale
    source: str  # "radar", "satellite", "model", "pilot_report"

@dataclass
class WeatherHazard:
    """Weather hazard assessment"""
    hazard_id: str
    hazard_type: str
    severity: str
    affected_area: Dict[str, Any]  # GeoJSON polygon
    altitude_range: Tuple[float, float]
    time_horizon: int  # minutes
    probability: float  # 0-1
    impact_level: str  # "low", "medium", "high", "critical"
    recommended_action: str
    alternative_routes: List[Dict[str, Any]]

@dataclass
class WeatherAvoidanceAction:
    """Weather avoidance action"""
    action_id: str
    aircraft_id: str
    action_type: str  # "route_change", "altitude_change", "delay", "diversion"
    current_route: List[Tuple[float, float]]
    recommended_route: List[Tuple[float, float]]
    current_altitude: float
    recommended_altitude: float
    delay_minutes: float
    reason: str
    weather_condition: str
    urgency: str  # "low", "medium", "high", "immediate"
    fuel_impact: float  # percentage
    time_impact: float  # minutes

class WeatherAvoidanceSystem:
    """Advanced weather avoidance system"""
    
    def __init__(self):
        # Weather thresholds
        self.weather_thresholds = {
            "thunderstorm": {
                "light": {"intensity": 0.3, "radius": 5, "avoidance_distance": 20},
                "moderate": {"intensity": 0.5, "radius": 10, "avoidance_distance": 30},
                "severe": {"intensity": 0.7, "radius": 15, "avoidance_distance": 50},
                "extreme": {"intensity": 0.9, "radius": 25, "avoidance_distance": 100}
            },
            "turbulence": {
                "light": {"intensity": 0.2, "radius": 3, "avoidance_distance": 10},
                "moderate": {"intensity": 0.4, "radius": 5, "avoidance_distance": 15},
                "severe": {"intensity": 0.6, "radius": 8, "avoidance_distance": 25},
                "extreme": {"intensity": 0.8, "radius": 12, "avoidance_distance": 40}
            },
            "icing": {
                "light": {"intensity": 0.3, "radius": 2, "avoidance_distance": 5},
                "moderate": {"intensity": 0.5, "radius": 4, "avoidance_distance": 10},
                "severe": {"intensity": 0.7, "radius": 6, "avoidance_distance": 15},
                "extreme": {"intensity": 0.9, "radius": 10, "avoidance_distance": 25}
            },
            "wind_shear": {
                "light": {"intensity": 0.2, "radius": 1, "avoidance_distance": 3},
                "moderate": {"intensity": 0.4, "radius": 2, "avoidance_distance": 5},
                "severe": {"intensity": 0.6, "radius": 3, "avoidance_distance": 8},
                "extreme": {"intensity": 0.8, "radius": 5, "avoidance_distance": 12}
            }
        }
        
        # Weather data sources
        self.data_sources = {
            "radar": "https://api.weather.gov/radar",
            "satellite": "https://api.weather.gov/satellite",
            "model": "https://api.weather.gov/model",
            "pilot_report": "https://api.faa.gov/pirep"
        }
        
        # Weather conditions database
        self.weather_conditions: Dict[str, WeatherCondition] = {}
        self.weather_hazards: Dict[str, WeatherHazard] = {}
        
        # Performance metrics
        self.conditions_processed = 0
        self.avoidance_actions_generated = 0
        self.routes_optimized = 0
        
        logger.info("Weather Avoidance System initialized")
    
    def load_weather_data(self, source: str = "all") -> bool:
        """Load weather data from sources"""
        
        try:
            if source == "all":
                for source_name in self.data_sources:
                    self._load_from_source(source_name)
            else:
                self._load_from_source(source)
            
            logger.info(f"Loaded {len(self.weather_conditions)} weather conditions")
            return True
            
        except Exception as e:
            logger.error(f"Error loading weather data: {e}")
            return False
    
    def _load_from_source(self, source: str):
        """Load weather data from specific source"""
        
        if source == "radar":
            self._load_radar_data()
        elif source == "satellite":
            self._load_satellite_data()
        elif source == "model":
            self._load_model_data()
        elif source == "pilot_report":
            self._load_pilot_reports()
    
    def _load_radar_data(self):
        """Load radar weather data"""
        
        # Simulate radar data for thunderstorms
        for i in range(5):
            condition = WeatherCondition(
                condition_id=f"RADAR_THUNDER_{i+1:03d}",
                condition_type="thunderstorm",
                severity=np.random.choice(["moderate", "severe", "extreme"]),
                latitude=40.0 + np.random.uniform(-5, 5),
                longitude=-75.0 + np.random.uniform(-5, 5),
                altitude_min=0,
                altitude_max=50000,
                radius=np.random.uniform(5, 25),
                intensity=np.random.uniform(0.3, 0.9),
                movement_direction=np.random.uniform(0, 360),
                movement_speed=np.random.uniform(20, 80),
                start_time=datetime.now(),
                end_time=datetime.now() + timedelta(hours=2),
                confidence=0.8,
                source="radar"
            )
            self.weather_conditions[condition.condition_id] = condition
    
    def _load_satellite_data(self):
        """Load satellite weather data"""
        
        # Simulate satellite data for turbulence
        for i in range(3):
            condition = WeatherCondition(
                condition_id=f"SAT_TURB_{i+1:03d}",
                condition_type="turbulence",
                severity=np.random.choice(["light", "moderate", "severe"]),
                latitude=35.0 + np.random.uniform(-3, 3),
                longitude=-80.0 + np.random.uniform(-3, 3),
                altitude_min=20000,
                altitude_max=45000,
                radius=np.random.uniform(3, 12),
                intensity=np.random.uniform(0.2, 0.8),
                movement_direction=np.random.uniform(0, 360),
                movement_speed=np.random.uniform(10, 50),
                start_time=datetime.now(),
                end_time=datetime.now() + timedelta(hours=4),
                confidence=0.7,
                source="satellite"
            )
            self.weather_conditions[condition.condition_id] = condition
    
    def _load_model_data(self):
        """Load weather model data"""
        
        # Simulate model data for icing conditions
        for i in range(4):
            condition = WeatherCondition(
                condition_id=f"MODEL_ICE_{i+1:03d}",
                condition_type="icing",
                severity=np.random.choice(["light", "moderate", "severe"]),
                latitude=45.0 + np.random.uniform(-2, 2),
                longitude=-100.0 + np.random.uniform(-2, 2),
                altitude_min=5000,
                altitude_max=25000,
                radius=np.random.uniform(2, 10),
                intensity=np.random.uniform(0.3, 0.9),
                movement_direction=np.random.uniform(0, 360),
                movement_speed=np.random.uniform(5, 30),
                start_time=datetime.now(),
                end_time=datetime.now() + timedelta(hours=6),
                confidence=0.6,
                source="model"
            )
            self.weather_conditions[condition.condition_id] = condition
    
    def _load_pilot_reports(self):
        """Load pilot weather reports"""
        
        # Simulate pilot reports for wind shear
        for i in range(2):
            condition = WeatherCondition(
                condition_id=f"PIREP_WIND_{i+1:03d}",
                condition_type="wind_shear",
                severity=np.random.choice(["moderate", "severe"]),
                latitude=30.0 + np.random.uniform(-1, 1),
                longitude=-90.0 + np.random.uniform(-1, 1),
                altitude_min=0,
                altitude_max=10000,
                radius=np.random.uniform(1, 5),
                intensity=np.random.uniform(0.4, 0.8),
                movement_direction=np.random.uniform(0, 360),
                movement_speed=np.random.uniform(0, 20),
                start_time=datetime.now(),
                end_time=datetime.now() + timedelta(hours=1),
                confidence=0.9,
                source="pilot_report"
            )
            self.weather_conditions[condition.condition_id] = condition
    
    def assess_weather_impact(self, route_coordinates: List[Tuple[float, float]], 
                            route_altitudes: List[float], 
                            time_horizon: int = 60) -> List[WeatherHazard]:
        """Assess weather impact on route"""
        
        hazards = []
        
        for condition in self.weather_conditions.values():
            if condition.end_time and condition.end_time < datetime.now():
                continue
            
            # Check if route intersects with weather condition
            impact = self._assess_condition_impact(condition, route_coordinates, route_altitudes, time_horizon)
            
            if impact:
                hazards.append(impact)
        
        # Sort by severity and impact
        hazards.sort(key=lambda x: (x.impact_level, x.probability), reverse=True)
        
        return hazards
    
    def _assess_condition_impact(self, condition: WeatherCondition, 
                               route_coordinates: List[Tuple[float, float]], 
                               route_altitudes: List[float], 
                               time_horizon: int) -> Optional[WeatherHazard]:
        """Assess impact of specific weather condition"""
        
        # Check if route intersects with weather condition
        intersection_points = []
        
        for i, (lat, lon) in enumerate(route_coordinates):
            alt = route_altitudes[i] if i < len(route_altitudes) else route_altitudes[0]
            
            # Check if point is within weather condition
            if self._point_in_weather_condition(lat, lon, alt, condition):
                intersection_points.append((lat, lon, alt))
        
        if not intersection_points:
            return None
        
        # Calculate impact level
        impact_level = self._calculate_impact_level(condition, len(intersection_points))
        
        # Generate affected area
        affected_area = self._generate_affected_area(intersection_points, condition)
        
        # Calculate probability
        probability = self._calculate_impact_probability(condition, intersection_points)
        
        # Recommend action
        recommended_action = self._recommend_weather_action(condition, impact_level)
        
        # Generate alternative routes
        alternative_routes = self._generate_weather_alternatives(route_coordinates, route_altitudes, condition)
        
        return WeatherHazard(
            hazard_id=f"HAZARD_{condition.condition_id}_{int(datetime.now().timestamp())}",
            hazard_type=condition.condition_type,
            severity=condition.severity,
            affected_area=affected_area,
            altitude_range=(condition.altitude_min, condition.altitude_max),
            time_horizon=time_horizon,
            probability=probability,
            impact_level=impact_level,
            recommended_action=recommended_action,
            alternative_routes=alternative_routes
        )
    
    def _point_in_weather_condition(self, lat: float, lon: float, alt: float, 
                                  condition: WeatherCondition) -> bool:
        """Check if point is within weather condition"""
        
        # Check altitude range
        if not (condition.altitude_min <= alt <= condition.altitude_max):
            return False
        
        # Check horizontal distance
        distance = self._calculate_distance(lat, lon, condition.latitude, condition.longitude)
        
        # Add avoidance distance based on severity
        threshold = self.weather_thresholds[condition.condition_type][condition.severity]["avoidance_distance"]
        
        return distance <= (condition.radius + threshold)
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in km"""
        
        # Haversine formula
        R = 6371  # Earth radius in km
        
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def _calculate_impact_level(self, condition: WeatherCondition, intersection_count: int) -> str:
        """Calculate impact level based on condition and intersections"""
        
        severity_scores = {"light": 1, "moderate": 2, "severe": 3, "extreme": 4}
        base_score = severity_scores[condition.severity]
        
        # Adjust based on intersection count
        if intersection_count >= 5:
            impact_score = base_score + 2
        elif intersection_count >= 3:
            impact_score = base_score + 1
        else:
            impact_score = base_score
        
        # Adjust based on intensity
        if condition.intensity > 0.8:
            impact_score += 1
        elif condition.intensity > 0.6:
            impact_score += 0.5
        
        # Determine impact level
        if impact_score >= 5:
            return "critical"
        elif impact_score >= 4:
            return "high"
        elif impact_score >= 3:
            return "medium"
        else:
            return "low"
    
    def _generate_affected_area(self, intersection_points: List[Tuple[float, float, float]], 
                              condition: WeatherCondition) -> Dict[str, Any]:
        """Generate affected area polygon"""
        
        if len(intersection_points) < 3:
            # Create simple circle around condition
            radius_deg = condition.radius / 111.0  # Convert km to degrees
            return {
                "type": "Polygon",
                "coordinates": [[
                    [condition.longitude - radius_deg, condition.latitude - radius_deg],
                    [condition.longitude + radius_deg, condition.latitude - radius_deg],
                    [condition.longitude + radius_deg, condition.latitude + radius_deg],
                    [condition.longitude - radius_deg, condition.latitude + radius_deg],
                    [condition.longitude - radius_deg, condition.latitude - radius_deg]
                ]]
            }
        
        # Create polygon from intersection points
        coords = [[point[1], point[0]] for point in intersection_points]  # lon, lat
        coords.append(coords[0])  # Close polygon
        
        return {
            "type": "Polygon",
            "coordinates": [coords]
        }
    
    def _calculate_impact_probability(self, condition: WeatherCondition, 
                                    intersection_points: List[Tuple[float, float, float]]) -> float:
        """Calculate probability of weather impact"""
        
        base_probability = condition.confidence
        
        # Adjust based on condition intensity
        intensity_factor = condition.intensity
        
        # Adjust based on number of intersection points
        intersection_factor = min(1.0, len(intersection_points) / 5.0)
        
        # Adjust based on severity
        severity_factors = {"light": 0.3, "moderate": 0.5, "severe": 0.7, "extreme": 0.9}
        severity_factor = severity_factors[condition.severity]
        
        probability = base_probability * intensity_factor * intersection_factor * severity_factor
        
        return min(1.0, max(0.0, probability))
    
    def _recommend_weather_action(self, condition: WeatherCondition, impact_level: str) -> str:
        """Recommend weather avoidance action"""
        
        if impact_level == "critical":
            return f"AVOID: Severe {condition.condition_type} - divert immediately"
        elif impact_level == "high":
            return f"CAUTION: {condition.condition_type.title()} - significant route deviation required"
        elif impact_level == "medium":
            return f"ADVISORY: {condition.condition_type.title()} - minor route adjustment recommended"
        else:
            return f"MONITOR: {condition.condition_type.title()} - continue with caution"
    
    def _generate_weather_alternatives(self, route_coordinates: List[Tuple[float, float]], 
                                     route_altitudes: List[float], 
                                     condition: WeatherCondition) -> List[Dict[str, Any]]:
        """Generate alternative routes to avoid weather"""
        
        alternatives = []
        
        # Get avoidance distance
        avoidance_distance = self.weather_thresholds[condition.condition_type][condition.severity]["avoidance_distance"]
        
        # Generate alternatives by offsetting route
        offset_distances = [avoidance_distance, avoidance_distance * 1.5, avoidance_distance * 2]
        
        for i, offset in enumerate(offset_distances):
            alt_route = []
            alt_altitudes = []
            
            for j, (lat, lon) in enumerate(route_coordinates):
                alt = route_altitudes[j] if j < len(route_altitudes) else route_altitudes[0]
                
                # Calculate offset direction (perpendicular to weather movement)
                offset_direction = (condition.movement_direction + 90) % 360
                
                # Apply offset
                offset_lat = lat + (offset / 111.0) * math.cos(math.radians(offset_direction))
                offset_lon = lon + (offset / 111.0) * math.sin(math.radians(offset_direction))
                
                alt_route.append((offset_lat, offset_lon))
                alt_altitudes.append(alt)
            
            # Assess alternative route
            alt_hazards = self.assess_weather_impact(alt_route, alt_altitudes)
            
            alternatives.append({
                "route_id": f"ALT_{i+1}",
                "coordinates": alt_route,
                "altitudes": alt_altitudes,
                "offset_distance": offset,
                "weather_hazards": len(alt_hazards),
                "max_impact": max([h.impact_level for h in alt_hazards]) if alt_hazards else "none",
                "estimated_delay": len(alt_hazards) * 5,  # 5 minutes per hazard
                "fuel_impact": len(alt_hazards) * 2  # 2% per hazard
            })
        
        return alternatives
    
    def generate_avoidance_actions(self, hazards: List[WeatherHazard], 
                                 aircraft_id: str, 
                                 current_route: List[Tuple[float, float]], 
                                 current_altitude: float) -> List[WeatherAvoidanceAction]:
        """Generate specific avoidance actions for weather hazards"""
        
        actions = []
        
        for hazard in hazards:
            if hazard.impact_level in ["high", "critical"]:
                # Generate route change action
                if hazard.alternative_routes:
                    best_alt = min(hazard.alternative_routes, key=lambda x: x["weather_hazards"])
                    
                    action = WeatherAvoidanceAction(
                        action_id=f"WEATHER_{aircraft_id}_{int(datetime.now().timestamp())}",
                        aircraft_id=aircraft_id,
                        action_type="route_change",
                        current_route=current_route,
                        recommended_route=best_alt["coordinates"],
                        current_altitude=current_altitude,
                        recommended_altitude=current_altitude,
                        delay_minutes=best_alt["estimated_delay"],
                        reason=f"Weather avoidance for {hazard.hazard_type}",
                        weather_condition=hazard.hazard_type,
                        urgency=hazard.impact_level,
                        fuel_impact=best_alt["fuel_impact"],
                        time_impact=best_alt["estimated_delay"]
                    )
                    actions.append(action)
                
                # Generate altitude change action if needed
                if hazard.altitude_range[0] <= current_altitude <= hazard.altitude_range[1]:
                    new_altitude = hazard.altitude_range[1] + 2000  # Climb above weather
                    
                    action = WeatherAvoidanceAction(
                        action_id=f"ALT_{aircraft_id}_{int(datetime.now().timestamp())}",
                        aircraft_id=aircraft_id,
                        action_type="altitude_change",
                        current_route=current_route,
                        recommended_route=current_route,
                        current_altitude=current_altitude,
                        recommended_altitude=new_altitude,
                        delay_minutes=10,
                        reason=f"Altitude change to avoid {hazard.hazard_type}",
                        weather_condition=hazard.hazard_type,
                        urgency=hazard.impact_level,
                        fuel_impact=5,
                        time_impact=10
                    )
                    actions.append(action)
        
        return actions
    
    def get_weather_forecast(self, lat: float, lon: float, alt: float, 
                           time_horizon: int = 60) -> Dict[str, Any]:
        """Get weather forecast for specific location"""
        
        forecast = {
            "location": {"latitude": lat, "longitude": lon, "altitude": alt},
            "time_horizon": time_horizon,
            "conditions": [],
            "hazards": [],
            "recommendations": []
        }
        
        # Check for weather conditions affecting this location
        for condition in self.weather_conditions.values():
            if self._point_in_weather_condition(lat, lon, alt, condition):
                forecast["conditions"].append({
                    "type": condition.condition_type,
                    "severity": condition.severity,
                    "intensity": condition.intensity,
                    "confidence": condition.confidence,
                    "movement": {
                        "direction": condition.movement_direction,
                        "speed": condition.movement_speed
                    }
                })
        
        # Generate recommendations
        if forecast["conditions"]:
            forecast["recommendations"] = [
                "Monitor weather conditions closely",
                "Consider alternative routing",
                "Maintain communication with ATC"
            ]
        
        return forecast
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get weather avoidance system status"""
        
        condition_types = {}
        severities = {}
        
        for condition in self.weather_conditions.values():
            condition_types[condition.condition_type] = condition_types.get(condition.condition_type, 0) + 1
            severities[condition.severity] = severities.get(condition.severity, 0) + 1
        
        return {
            "system_status": "operational",
            "total_conditions": len(self.weather_conditions),
            "active_conditions": len([c for c in self.weather_conditions.values() if not c.end_time or c.end_time > datetime.now()]),
            "condition_types": condition_types,
            "severities": severities,
            "conditions_processed": self.conditions_processed,
            "avoidance_actions_generated": self.avoidance_actions_generated,
            "routes_optimized": self.routes_optimized,
            "last_update": datetime.now().isoformat()
        }

def main():
    """Test the weather avoidance system"""
    
    # Initialize weather avoidance system
    system = WeatherAvoidanceSystem()
    
    # Load weather data
    system.load_weather_data()
    
    # Test route
    test_route = [
        (40.7128, -74.0060),  # New York
        (40.6892, -74.0445),  # Statue of Liberty
        (40.7589, -73.9851)   # Times Square
    ]
    test_altitudes = [35000, 35000, 35000]
    
    # Assess weather impact
    hazards = system.assess_weather_impact(test_route, test_altitudes)
    
    print(f"Weather Impact Assessment:")
    print(f"Total Hazards: {len(hazards)}")
    
    for hazard in hazards:
        print(f"Hazard: {hazard.hazard_type} ({hazard.severity})")
        print(f"Impact Level: {hazard.impact_level}")
        print(f"Probability: {hazard.probability:.2f}")
        print(f"Action: {hazard.recommended_action}")
        print(f"Alternative Routes: {len(hazard.alternative_routes)}")
        print()
    
    # Generate avoidance actions
    actions = system.generate_avoidance_actions(hazards, "TEST_AIRCRAFT", test_route, 35000)
    
    print(f"Generated {len(actions)} avoidance actions:")
    for action in actions:
        print(f"Action: {action.action_type}")
        print(f"Urgency: {action.urgency}")
        print(f"Delay: {action.delay_minutes} minutes")
        print(f"Fuel Impact: {action.fuel_impact}%")
        print()
    
    # Get system status
    status = system.get_system_status()
    print(f"System Status:")
    print(f"Active Conditions: {status['active_conditions']}")
    print(f"Condition Types: {status['condition_types']}")

if __name__ == "__main__":
    main()



