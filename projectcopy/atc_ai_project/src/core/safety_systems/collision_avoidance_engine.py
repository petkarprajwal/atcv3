#!/usr/bin/env python3
"""
Collision Avoidance Engine
Advanced collision detection and avoidance system for ATC AI
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
import logging
import math
from scipy.spatial.distance import cdist
from scipy.optimize import minimize
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Aircraft:
    """Aircraft data structure"""
    icao24: str
    callsign: str
    latitude: float
    longitude: float
    altitude: float
    velocity: float
    heading: float
    vertical_rate: float
    timestamp: datetime
    aircraft_type: str = "UNKNOWN"
    priority: int = 1  # 1=normal, 2=priority, 3=emergency

@dataclass
class Conflict:
    """Conflict detection result"""
    conflict_id: str
    aircraft1: str
    aircraft2: str
    conflict_type: str  # "horizontal", "vertical", "combined"
    severity: str  # "low", "medium", "high", "critical"
    time_to_conflict: float  # seconds
    separation_distance: float  # meters
    recommended_action: str
    confidence: float
    timestamp: datetime

@dataclass
class AvoidanceAction:
    """Recommended avoidance action"""
    action_id: str
    aircraft_id: str
    action_type: str  # "altitude_change", "heading_change", "speed_change", "vector"
    current_value: float
    recommended_value: float
    urgency: str  # "low", "medium", "high", "immediate"
    reason: str
    estimated_impact: Dict[str, Any]

class CollisionAvoidanceEngine:
    """Advanced collision avoidance system"""
    
    def __init__(self):
        # Separation standards (ICAO/FAA compliant)
        self.separation_standards = {
            "horizontal": {
                "en_route": 5.0,  # 5 nautical miles
                "terminal": 3.0,   # 3 nautical miles
                "approach": 2.5,   # 2.5 nautical miles
                "departure": 3.0   # 3 nautical miles
            },
            "vertical": {
                "en_route": 1000,  # 1000 feet
                "terminal": 1000,  # 1000 feet
                "approach": 500,   # 500 feet
                "departure": 1000  # 1000 feet
            },
            "time": {
                "minimum": 60,     # 60 seconds minimum
                "preferred": 120,  # 120 seconds preferred
                "critical": 30     # 30 seconds critical
            }
        }
        
        # Conflict detection parameters
        self.detection_horizon = 900  # 15 minutes in seconds
        self.update_interval = 5      # 5 seconds
        self.prediction_steps = 180   # 180 steps for 15 minutes
        
        # Performance metrics
        self.conflicts_detected = 0
        self.conflicts_resolved = 0
        self.false_alarms = 0
        
        logger.info("Collision Avoidance Engine initialized")
    
    def detect_conflicts(self, aircraft_list: List[Aircraft]) -> List[Conflict]:
        """Detect potential conflicts between aircraft"""
        
        conflicts = []
        current_time = datetime.now()
        
        # Convert aircraft list to DataFrame for easier processing
        aircraft_df = self._prepare_aircraft_data(aircraft_list)
        
        if len(aircraft_df) < 2:
            return conflicts
        
        # Check all aircraft pairs
        for i in range(len(aircraft_df)):
            for j in range(i + 1, len(aircraft_df)):
                aircraft1 = aircraft_df.iloc[i]
                aircraft2 = aircraft_df.iloc[j]
                
                # Predict trajectories
                traj1 = self._predict_trajectory(aircraft1, self.prediction_steps)
                traj2 = self._predict_trajectory(aircraft2, self.prediction_steps)
                
                # Check for conflicts
                conflict = self._check_trajectory_conflict(
                    aircraft1, aircraft2, traj1, traj2, current_time
                )
                
                if conflict:
                    conflicts.append(conflict)
                    self.conflicts_detected += 1
        
        # Sort conflicts by severity and time
        conflicts.sort(key=lambda x: (x.severity, x.time_to_conflict))
        
        logger.info(f"Detected {len(conflicts)} potential conflicts")
        return conflicts
    
    def _prepare_aircraft_data(self, aircraft_list: List[Aircraft]) -> pd.DataFrame:
        """Prepare aircraft data for processing"""
        
        data = []
        for aircraft in aircraft_list:
            data.append({
                'icao24': aircraft.icao24,
                'callsign': aircraft.callsign,
                'latitude': aircraft.latitude,
                'longitude': aircraft.longitude,
                'altitude': aircraft.altitude,
                'velocity': aircraft.velocity,
                'heading': aircraft.heading,
                'vertical_rate': aircraft.vertical_rate,
                'aircraft_type': aircraft.aircraft_type,
                'priority': aircraft.priority
            })
        
        return pd.DataFrame(data)
    
    def _predict_trajectory(self, aircraft: pd.Series, steps: int) -> np.ndarray:
        """Predict aircraft trajectory"""
        
        # Current position
        lat = aircraft['latitude']
        lon = aircraft['longitude']
        alt = aircraft['altitude']
        vel = aircraft['velocity']  # knots
        hdg = aircraft['heading']   # degrees
        vrate = aircraft['vertical_rate']  # feet per minute
        
        # Convert to meters per second
        vel_ms = vel * 0.514444  # knots to m/s
        vrate_ms = vrate * 0.00508  # ft/min to m/s
        
        # Earth radius in meters
        R = 6371000
        
        trajectory = []
        
        for step in range(steps):
            # Time step
            dt = self.update_interval
            
            # Convert heading to radians
            hdg_rad = math.radians(hdg)
            
            # Calculate new position
            # Horizontal movement
            lat_delta = (vel_ms * math.cos(hdg_rad) * dt) / R
            lon_delta = (vel_ms * math.sin(hdg_rad) * dt) / (R * math.cos(math.radians(lat)))
            
            # Vertical movement
            alt_delta = vrate_ms * dt
            
            # Update position
            lat += math.degrees(lat_delta)
            lon += math.degrees(lon_delta)
            alt += alt_delta
            
            trajectory.append([lat, lon, alt])
        
        return np.array(trajectory)
    
    def _check_trajectory_conflict(self, aircraft1: pd.Series, aircraft2: pd.Series, 
                                 traj1: np.ndarray, traj2: np.ndarray, 
                                 current_time: datetime) -> Optional[Conflict]:
        """Check if two trajectories have a conflict"""
        
        # Calculate distances at each time step
        for i, (pos1, pos2) in enumerate(zip(traj1, traj2)):
            # Calculate horizontal distance
            h_dist = self._calculate_horizontal_distance(pos1, pos2)
            
            # Calculate vertical distance
            v_dist = abs(pos1[2] - pos2[2])
            
            # Time to conflict
            time_to_conflict = i * self.update_interval
            
            # Check separation standards
            h_separation = self._get_horizontal_separation(aircraft1, aircraft2)
            v_separation = self._get_vertical_separation(aircraft1, aircraft2)
            
            # Check for conflict
            if h_dist < h_separation and v_dist < v_separation:
                # Determine conflict type and severity
                conflict_type = self._determine_conflict_type(h_dist, v_dist, h_separation, v_separation)
                severity = self._determine_severity(h_dist, v_dist, time_to_conflict)
                
                # Generate conflict ID
                conflict_id = f"CONF_{aircraft1['icao24']}_{aircraft2['icao24']}_{int(current_time.timestamp())}"
                
                # Recommend action
                recommended_action = self._recommend_avoidance_action(
                    aircraft1, aircraft2, pos1, pos2, severity
                )
                
                # Calculate confidence
                confidence = self._calculate_confidence(h_dist, v_dist, time_to_conflict)
                
                return Conflict(
                    conflict_id=conflict_id,
                    aircraft1=aircraft1['icao24'],
                    aircraft2=aircraft2['icao24'],
                    conflict_type=conflict_type,
                    severity=severity,
                    time_to_conflict=time_to_conflict,
                    separation_distance=min(h_dist, v_dist),
                    recommended_action=recommended_action,
                    confidence=confidence,
                    timestamp=current_time
                )
        
        return None
    
    def _calculate_horizontal_distance(self, pos1: np.ndarray, pos2: np.ndarray) -> float:
        """Calculate horizontal distance between two positions"""
        
        # Haversine formula for great circle distance
        lat1, lon1 = math.radians(pos1[0]), math.radians(pos1[1])
        lat2, lon2 = math.radians(pos2[0]), math.radians(pos2[1])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth radius in nautical miles
        R_nm = 3440.065
        distance_nm = R_nm * c
        
        return distance_nm
    
    def _get_horizontal_separation(self, aircraft1: pd.Series, aircraft2: pd.Series) -> float:
        """Get required horizontal separation"""
        
        # Determine airspace type based on altitude
        alt1 = aircraft1['altitude']
        alt2 = aircraft2['altitude']
        avg_alt = (alt1 + alt2) / 2
        
        if avg_alt < 10000:  # Terminal airspace
            return self.separation_standards["horizontal"]["terminal"]
        else:  # En-route airspace
            return self.separation_standards["horizontal"]["en_route"]
    
    def _get_vertical_separation(self, aircraft1: pd.Series, aircraft2: pd.Series) -> float:
        """Get required vertical separation in feet"""
        
        # Determine airspace type based on altitude
        alt1 = aircraft1['altitude']
        alt2 = aircraft2['altitude']
        avg_alt = (alt1 + alt2) / 2
        
        if avg_alt < 10000:  # Terminal airspace
            return self.separation_standards["vertical"]["terminal"]
        else:  # En-route airspace
            return self.separation_standards["vertical"]["en_route"]
    
    def _determine_conflict_type(self, h_dist: float, v_dist: float, 
                               h_separation: float, v_separation: float) -> str:
        """Determine type of conflict"""
        
        if h_dist < h_separation and v_dist < v_separation:
            return "combined"
        elif h_dist < h_separation:
            return "horizontal"
        else:
            return "vertical"
    
    def _determine_severity(self, h_dist: float, v_dist: float, time_to_conflict: float) -> str:
        """Determine conflict severity"""
        
        # Critical: Very close and imminent
        if h_dist < 1.0 and v_dist < 200 and time_to_conflict < 60:
            return "critical"
        
        # High: Close and soon
        elif h_dist < 2.0 and v_dist < 500 and time_to_conflict < 180:
            return "high"
        
        # Medium: Moderate separation and time
        elif h_dist < 3.0 and v_dist < 800 and time_to_conflict < 300:
            return "medium"
        
        # Low: Adequate separation or time
        else:
            return "low"
    
    def _recommend_avoidance_action(self, aircraft1: pd.Series, aircraft2: pd.Series,
                                  pos1: np.ndarray, pos2: np.ndarray, severity: str) -> str:
        """Recommend avoidance action"""
        
        # Priority-based recommendations
        if aircraft1['priority'] > aircraft2['priority']:
            primary_aircraft = aircraft1
            secondary_aircraft = aircraft2
        else:
            primary_aircraft = aircraft2
            secondary_aircraft = aircraft1
        
        if severity == "critical":
            return f"IMMEDIATE: {secondary_aircraft['callsign']} turn right 30 degrees, climb 1000 feet"
        elif severity == "high":
            return f"URGENT: {secondary_aircraft['callsign']} turn right 20 degrees, climb 500 feet"
        elif severity == "medium":
            return f"ADVISORY: {secondary_aircraft['callsign']} turn right 15 degrees"
        else:
            return f"MONITOR: Continue current heading, maintain separation"
    
    def _calculate_confidence(self, h_dist: float, v_dist: float, time_to_conflict: float) -> float:
        """Calculate confidence in conflict prediction"""
        
        # Base confidence on distance and time
        distance_factor = max(0, 1 - (h_dist / 5.0))  # Closer = higher confidence
        time_factor = max(0, 1 - (time_to_conflict / 900))  # Sooner = higher confidence
        
        confidence = (distance_factor + time_factor) / 2
        return min(1.0, max(0.0, confidence))
    
    def generate_avoidance_actions(self, conflicts: List[Conflict], 
                                 aircraft_list: List[Aircraft]) -> List[AvoidanceAction]:
        """Generate specific avoidance actions for conflicts"""
        
        actions = []
        
        for conflict in conflicts:
            # Find aircraft involved
            aircraft1 = next((a for a in aircraft_list if a.icao24 == conflict.aircraft1), None)
            aircraft2 = next((a for a in aircraft_list if a.icao24 == conflict.aircraft2), None)
            
            if not aircraft1 or not aircraft2:
                continue
            
            # Determine which aircraft should take action
            action_aircraft = aircraft2 if aircraft1.priority >= aircraft2.priority else aircraft1
            
            # Generate specific actions based on conflict type
            if conflict.conflict_type == "horizontal":
                action = self._generate_horizontal_avoidance(action_aircraft, conflict)
            elif conflict.conflict_type == "vertical":
                action = self._generate_vertical_avoidance(action_aircraft, conflict)
            else:  # combined
                action = self._generate_combined_avoidance(action_aircraft, conflict)
            
            if action:
                actions.append(action)
        
        return actions
    
    def _generate_horizontal_avoidance(self, aircraft: Aircraft, conflict: Conflict) -> AvoidanceAction:
        """Generate horizontal avoidance action"""
        
        # Calculate required heading change
        current_heading = aircraft.heading
        recommended_heading = (current_heading + 30) % 360  # Turn right 30 degrees
        
        return AvoidanceAction(
            action_id=f"HDG_{aircraft.icao24}_{int(datetime.now().timestamp())}",
            aircraft_id=aircraft.icao24,
            action_type="heading_change",
            current_value=current_heading,
            recommended_value=recommended_heading,
            urgency=conflict.severity,
            reason=f"Horizontal separation conflict with {conflict.aircraft1 if conflict.aircraft1 != aircraft.icao24 else conflict.aircraft2}",
            estimated_impact={
                "fuel_impact": "minimal",
                "time_impact": "2-5 minutes",
                "safety_improvement": "high"
            }
        )
    
    def _generate_vertical_avoidance(self, aircraft: Aircraft, conflict: Conflict) -> AvoidanceAction:
        """Generate vertical avoidance action"""
        
        # Calculate required altitude change
        current_altitude = aircraft.altitude
        recommended_altitude = current_altitude + 1000  # Climb 1000 feet
        
        return AvoidanceAction(
            action_id=f"ALT_{aircraft.icao24}_{int(datetime.now().timestamp())}",
            aircraft_id=aircraft.icao24,
            action_type="altitude_change",
            current_value=current_altitude,
            recommended_value=recommended_altitude,
            urgency=conflict.severity,
            reason=f"Vertical separation conflict with {conflict.aircraft1 if conflict.aircraft1 != aircraft.icao24 else conflict.aircraft2}",
            estimated_impact={
                "fuel_impact": "moderate",
                "time_impact": "3-7 minutes",
                "safety_improvement": "high"
            }
        )
    
    def _generate_combined_avoidance(self, aircraft: Aircraft, conflict: Conflict) -> AvoidanceAction:
        """Generate combined avoidance action"""
        
        # For combined conflicts, prioritize altitude change
        current_altitude = aircraft.altitude
        recommended_altitude = current_altitude + 1000  # Climb 1000 feet
        
        return AvoidanceAction(
            action_id=f"COMBO_{aircraft.icao24}_{int(datetime.now().timestamp())}",
            aircraft_id=aircraft.icao24,
            action_type="altitude_change",
            current_value=current_altitude,
            recommended_value=recommended_altitude,
            urgency=conflict.severity,
            reason=f"Combined separation conflict with {conflict.aircraft1 if conflict.aircraft1 != aircraft.icao24 else conflict.aircraft2}",
            estimated_impact={
                "fuel_impact": "moderate",
                "time_impact": "5-10 minutes",
                "safety_improvement": "critical"
            }
        )
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get collision avoidance system status"""
        
        return {
            "system_status": "operational",
            "conflicts_detected": self.conflicts_detected,
            "conflicts_resolved": self.conflicts_resolved,
            "false_alarms": self.false_alarms,
            "detection_horizon": self.detection_horizon,
            "update_interval": self.update_interval,
            "separation_standards": self.separation_standards,
            "last_update": datetime.now().isoformat()
        }
    
    def update_separation_standards(self, new_standards: Dict[str, Any]):
        """Update separation standards"""
        
        self.separation_standards.update(new_standards)
        logger.info("Separation standards updated")
    
    def reset_metrics(self):
        """Reset performance metrics"""
        
        self.conflicts_detected = 0
        self.conflicts_resolved = 0
        self.false_alarms = 0
        logger.info("Performance metrics reset")

def main():
    """Test the collision avoidance engine"""
    
    # Create test aircraft
    aircraft1 = Aircraft(
        icao24="ABC123",
        callsign="FL123",
        latitude=40.7128,
        longitude=-74.0060,
        altitude=35000,
        velocity=500,
        heading=90,
        vertical_rate=0,
        timestamp=datetime.now()
    )
    
    aircraft2 = Aircraft(
        icao24="DEF456",
        callsign="FL456",
        latitude=40.7200,
        longitude=-73.9900,
        altitude=35000,
        velocity=500,
        heading=270,
        vertical_rate=0,
        timestamp=datetime.now()
    )
    
    # Initialize collision avoidance engine
    engine = CollisionAvoidanceEngine()
    
    # Detect conflicts
    conflicts = engine.detect_conflicts([aircraft1, aircraft2])
    
    print(f"Detected {len(conflicts)} conflicts")
    for conflict in conflicts:
        print(f"Conflict: {conflict.aircraft1} vs {conflict.aircraft2}")
        print(f"Type: {conflict.conflict_type}, Severity: {conflict.severity}")
        print(f"Time to conflict: {conflict.time_to_conflict}s")
        print(f"Action: {conflict.recommended_action}")
        print()
    
    # Generate avoidance actions
    actions = engine.generate_avoidance_actions(conflicts, [aircraft1, aircraft2])
    
    print(f"Generated {len(actions)} avoidance actions")
    for action in actions:
        print(f"Action: {action.action_type} for {action.aircraft_id}")
        print(f"Current: {action.current_value}, Recommended: {action.recommended_value}")
        print(f"Urgency: {action.urgency}")
        print()

if __name__ == "__main__":
    main()



