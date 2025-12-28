#!/usr/bin/env python3
"""
Real-Time Conflict Detection System for Dashboard Integration
Live conflict analysis with probability visualization and alerts
"""

import numpy as np
import pandas as pd
import math
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class LiveConflictAlert:
    """Real-time conflict alert structure"""
    alert_id: str
    aircraft_1: str
    aircraft_2: str
    conflict_probability: float
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    time_to_conflict: float  # seconds
    separation_distance: float  # nautical miles
    altitude_separation: float  # feet
    relative_speed: float  # knots
    conflict_location: Tuple[float, float, float]  # lat, lon, alt
    resolution_actions: List[str]
    detection_time: datetime
    confidence_score: float

class RealTimeConflictDetector:
    """Advanced real-time conflict detection for live flight data"""
    
    def __init__(self):
        """Initialize the conflict detection system"""
        
        # Safety parameters (ICAO standards)
        self.min_horizontal_separation = 5.0  # nautical miles
        self.min_vertical_separation = 1000.0  # feet
        self.prediction_horizon = 1800  # 30 minutes in seconds
        
        # Risk assessment thresholds
        self.risk_thresholds = {
            'CRITICAL': 0.85,  # >85% conflict probability
            'HIGH': 0.65,      # 65-85% conflict probability  
            'MEDIUM': 0.35,    # 35-65% conflict probability
            'LOW': 0.15        # 15-35% conflict probability
        }
        
        # Conflict detection cache
        self.conflict_cache = {}
        self.last_detection_time = None
        
    def detect_conflicts(self, flights_df: pd.DataFrame) -> List[LiveConflictAlert]:
        """
        Detect potential conflicts in real-time flight data
        
        Args:
            flights_df: DataFrame with current flight positions and vectors
            
        Returns:
            List of conflict alerts sorted by risk level
        """
        
        if flights_df.empty or len(flights_df) < 2:
            return []
        
        current_time = datetime.now()
        conflicts = []
        
        # Filter for flights with complete trajectory data
        valid_flights = flights_df.dropna(subset=[
            'latitude', 'longitude', 'baro_altitude', 'velocity', 'true_track'
        ])
        
        if len(valid_flights) < 2:
            return []
        
        # Pairwise conflict detection
        for i in range(len(valid_flights)):
            for j in range(i + 1, len(valid_flights)):
                flight_1 = valid_flights.iloc[i]
                flight_2 = valid_flights.iloc[j]
                
                # Skip if same aircraft
                if flight_1['callsign'] == flight_2['callsign']:
                    continue
                
                # Analyze potential conflict
                conflict_alert = self._analyze_aircraft_pair(flight_1, flight_2, current_time)
                
                if conflict_alert and conflict_alert.conflict_probability > 0.1:  # Only report >10% probability
                    conflicts.append(conflict_alert)
        
        # Sort by risk level and time to conflict
        conflicts.sort(key=lambda x: (-x.conflict_probability, x.time_to_conflict))
        
        # Update cache
        self.conflict_cache = {alert.alert_id: alert for alert in conflicts}
        self.last_detection_time = current_time
        
        return conflicts[:20]  # Return top 20 conflicts
    
    def _analyze_aircraft_pair(self, flight_1: pd.Series, flight_2: pd.Series, 
                              current_time: datetime) -> Optional[LiveConflictAlert]:
        """Analyze a pair of aircraft for potential conflicts"""
        
        try:
            # Extract current positions and velocities
            pos1 = (flight_1['latitude'], flight_1['longitude'], flight_1['baro_altitude'])
            pos2 = (flight_2['latitude'], flight_2['longitude'], flight_2['baro_altitude'])
            
            vel1 = (flight_1['velocity'], flight_1['true_track'], 
                   flight_1.get('vertical_rate', 0))
            vel2 = (flight_2['velocity'], flight_2['true_track'], 
                   flight_2.get('vertical_rate', 0))
            
            # Calculate current separation
            horizontal_sep = self._calculate_horizontal_distance(pos1, pos2)
            vertical_sep = abs(pos1[2] - pos2[2])
            
            # Skip if already well separated
            if horizontal_sep > 50.0 or vertical_sep > 5000.0:  # 50nm or 5000ft
                return None
            
            # Predict future positions and find closest approach
            closest_approach = self._find_closest_approach(pos1, vel1, pos2, vel2)
            
            if not closest_approach:
                return None
            
            time_to_closest, min_separation, approach_altitude_sep, approach_location = closest_approach
            
            # Calculate conflict probability
            conflict_prob = self._calculate_conflict_probability(
                min_separation, approach_altitude_sep, time_to_closest, vel1, vel2
            )
            
            # Skip low probability conflicts in busy airspace
            if conflict_prob < 0.1:
                return None
            
            # Determine risk level
            risk_level = self._determine_risk_level(conflict_prob)
            
            # Calculate relative speed
            relative_speed = self._calculate_relative_speed(vel1, vel2)
            
            # Generate resolution actions
            resolution_actions = self._generate_resolution_actions(
                flight_1, flight_2, min_separation, approach_altitude_sep, time_to_closest
            )
            
            # Create conflict alert
            alert_id = f"CONF_{flight_1['callsign']}_{flight_2['callsign']}_{int(current_time.timestamp())}"
            
            return LiveConflictAlert(
                alert_id=alert_id,
                aircraft_1=flight_1['callsign'],
                aircraft_2=flight_2['callsign'],
                conflict_probability=conflict_prob,
                risk_level=risk_level,
                time_to_conflict=time_to_closest,
                separation_distance=min_separation,
                altitude_separation=approach_altitude_sep,
                relative_speed=relative_speed,
                conflict_location=approach_location,
                resolution_actions=resolution_actions,
                detection_time=current_time,
                confidence_score=min(0.95, conflict_prob + 0.1)
            )
            
        except Exception as e:
            logger.error(f"Error analyzing aircraft pair: {e}")
            return None
    
    def _calculate_horizontal_distance(self, pos1: Tuple, pos2: Tuple) -> float:
        """Calculate horizontal distance in nautical miles"""
        
        lat1, lon1, _ = pos1
        lat2, lon2, _ = pos2
        
        # Haversine formula
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(dlon/2)**2)
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth radius in nautical miles
        earth_radius_nm = 3440.065
        
        return c * earth_radius_nm
    
    def _find_closest_approach(self, pos1: Tuple, vel1: Tuple, pos2: Tuple, vel2: Tuple) -> Optional[Tuple]:
        """Find the closest approach point between two aircraft"""
        
        try:
            # Extract positions and velocities
            lat1, lon1, alt1 = pos1
            lat2, lon2, alt2 = pos2
            speed1, track1, climb_rate1 = vel1
            speed2, track2, climb_rate2 = vel2
            
            # Convert to Cartesian coordinates for easier calculation
            # (Simplified - assumes small area, flat earth approximation)
            
            # Calculate velocity components (nautical miles per second)
            v1_x = speed1 * math.sin(math.radians(track1)) / 3600
            v1_y = speed1 * math.cos(math.radians(track1)) / 3600
            v1_z = climb_rate1 / 60  # feet per second
            
            v2_x = speed2 * math.sin(math.radians(track2)) / 3600
            v2_y = speed2 * math.cos(math.radians(track2)) / 3600
            v2_z = climb_rate2 / 60  # feet per second
            
            # Relative velocity
            rel_vx = v1_x - v2_x
            rel_vy = v1_y - v2_y
            rel_vz = v1_z - v2_z
            
            # Initial separation in approximate Cartesian coordinates
            # (rough conversion for small distances)
            dx = (lon1 - lon2) * 60  # nautical miles
            dy = (lat1 - lat2) * 60  # nautical miles
            dz = alt1 - alt2  # feet
            
            # Time to closest approach (assuming constant velocity)
            rel_speed_squared = rel_vx**2 + rel_vy**2
            
            if rel_speed_squared < 1e-6:  # Aircraft moving in parallel
                # Calculate current separation
                horizontal_sep = math.sqrt(dx**2 + dy**2)
                return (0, horizontal_sep, abs(dz), (lat1, lon1, alt1))
            
            # Time to closest approach in horizontal plane
            t_closest = -(dx * rel_vx + dy * rel_vy) / rel_speed_squared
            
            # Limit prediction horizon
            t_closest = max(0, min(t_closest, self.prediction_horizon))
            
            # Calculate positions at closest approach
            future_dx = dx + rel_vx * t_closest
            future_dy = dy + rel_vy * t_closest
            future_dz = dz + rel_vz * t_closest
            
            # Minimum horizontal separation
            min_horizontal_sep = math.sqrt(future_dx**2 + future_dy**2)
            
            # Future positions
            future_lat1 = lat1 + v1_y * t_closest / 60
            future_lon1 = lon1 + v1_x * t_closest / 60
            future_alt1 = alt1 + v1_z * t_closest
            
            approach_location = (future_lat1, future_lon1, future_alt1)
            
            return (t_closest, min_horizontal_sep, abs(future_dz), approach_location)
            
        except Exception as e:
            logger.error(f"Error calculating closest approach: {e}")
            return None
    
    def _calculate_conflict_probability(self, min_separation: float, altitude_sep: float,
                                      time_to_conflict: float, vel1: Tuple, vel2: Tuple) -> float:
        """Calculate conflict probability based on multiple factors"""
        
        # Base probability based on separation
        if min_separation < self.min_horizontal_separation and altitude_sep < self.min_vertical_separation:
            base_prob = 1.0  # Definite conflict
        else:
            # Inverse relationship with separation
            horizontal_factor = max(0, 1 - (min_separation / (self.min_horizontal_separation * 2)))
            vertical_factor = max(0, 1 - (altitude_sep / (self.min_vertical_separation * 2)))
            base_prob = (horizontal_factor + vertical_factor) / 2
        
        # Time factor (higher probability for near-term conflicts)
        time_factor = max(0.1, 1 - (time_to_conflict / self.prediction_horizon))
        
        # Speed factor (higher relative speeds increase uncertainty)
        relative_speed = self._calculate_relative_speed(vel1, vel2)
        speed_factor = min(1.0, 1 + (relative_speed - 200) / 1000)  # Normalize around 200kt
        
        # Combine factors
        probability = base_prob * time_factor * speed_factor
        
        # Apply uncertainty for longer predictions
        if time_to_conflict > 600:  # 10 minutes
            uncertainty_reduction = 1 - ((time_to_conflict - 600) / self.prediction_horizon)
            probability *= uncertainty_reduction
        
        return max(0.0, min(1.0, probability))
    
    def _calculate_relative_speed(self, vel1: Tuple, vel2: Tuple) -> float:
        """Calculate relative speed between two aircraft"""
        
        speed1, track1, _ = vel1
        speed2, track2, _ = vel2
        
        # Calculate velocity components
        v1_x = speed1 * math.sin(math.radians(track1))
        v1_y = speed1 * math.cos(math.radians(track1))
        v2_x = speed2 * math.sin(math.radians(track2))
        v2_y = speed2 * math.cos(math.radians(track2))
        
        # Relative velocity magnitude
        rel_vx = v1_x - v2_x
        rel_vy = v1_y - v2_y
        
        return math.sqrt(rel_vx**2 + rel_vy**2)
    
    def _determine_risk_level(self, probability: float) -> str:
        """Determine risk level based on conflict probability"""
        
        if probability >= self.risk_thresholds['CRITICAL']:
            return 'CRITICAL'
        elif probability >= self.risk_thresholds['HIGH']:
            return 'HIGH'
        elif probability >= self.risk_thresholds['MEDIUM']:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _generate_resolution_actions(self, flight_1: pd.Series, flight_2: pd.Series,
                                   min_separation: float, altitude_sep: float,
                                   time_to_conflict: float) -> List[str]:
        """Generate conflict resolution suggestions"""
        
        actions = []
        
        # Determine primary resolution based on separation type
        if altitude_sep < self.min_vertical_separation:
            # Vertical separation needed
            if flight_1['baro_altitude'] > flight_2['baro_altitude']:
                actions.append(f"🔺 {flight_1['callsign']}: Climb to maintain separation")
                actions.append(f"🔻 {flight_2['callsign']}: Descend to maintain separation")
            else:
                actions.append(f"🔺 {flight_2['callsign']}: Climb to maintain separation")
                actions.append(f"🔻 {flight_1['callsign']}: Descend to maintain separation")
        
        if min_separation < self.min_horizontal_separation:
            # Horizontal separation needed
            actions.append(f"↪️ {flight_1['callsign']}: Turn right 15° for 2 minutes")
            actions.append(f"↩️ {flight_2['callsign']}: Turn left 15° for 2 minutes")
            
            # Speed adjustments
            if flight_1['velocity'] > flight_2['velocity']:
                actions.append(f"🐌 {flight_1['callsign']}: Reduce speed by 20 knots")
            else:
                actions.append(f"🐌 {flight_2['callsign']}: Reduce speed by 20 knots")
        
        # Time-critical actions
        if time_to_conflict < 300:  # 5 minutes
            actions.append("⚠️ IMMEDIATE ATC INTERVENTION REQUIRED")
        elif time_to_conflict < 600:  # 10 minutes
            actions.append("🔔 Alert pilots and prepare for vector changes")
        
        return actions[:5]  # Limit to 5 most important actions

def get_conflict_summary_stats(conflicts: List[LiveConflictAlert]) -> Dict:
    """Generate summary statistics for conflicts"""
    
    if not conflicts:
        return {
            'total_conflicts': 0,
            'critical_conflicts': 0,
            'high_risk_conflicts': 0,
            'avg_time_to_conflict': 0,
            'min_separation': 0,
            'aircraft_involved': 0
        }
    
    # Count by risk level
    risk_counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
    for conflict in conflicts:
        risk_counts[conflict.risk_level] += 1
    
    # Calculate statistics
    avg_time = sum(c.time_to_conflict for c in conflicts) / len(conflicts)
    min_sep = min(c.separation_distance for c in conflicts)
    
    # Count unique aircraft involved
    aircraft_involved = set()
    for conflict in conflicts:
        aircraft_involved.add(conflict.aircraft_1)
        aircraft_involved.add(conflict.aircraft_2)
    
    return {
        'total_conflicts': len(conflicts),
        'critical_conflicts': risk_counts['CRITICAL'],
        'high_risk_conflicts': risk_counts['HIGH'],
        'medium_risk_conflicts': risk_counts['MEDIUM'],
        'low_risk_conflicts': risk_counts['LOW'],
        'avg_time_to_conflict': avg_time,
        'min_separation': min_sep,
        'aircraft_involved': len(aircraft_involved),
        'detection_time': conflicts[0].detection_time if conflicts else datetime.now()
    }

# Test function for development
def test_conflict_detection():
    """Test the conflict detection system with sample data"""
    
    # Create sample flight data
    sample_flights = pd.DataFrame([
        {
            'callsign': 'UAL123', 'latitude': 40.7128, 'longitude': -74.0060,
            'baro_altitude': 35000, 'velocity': 450, 'true_track': 90, 'vertical_rate': 0
        },
        {
            'callsign': 'AAL456', 'latitude': 40.7500, 'longitude': -73.9000,
            'baro_altitude': 35500, 'velocity': 440, 'true_track': 270, 'vertical_rate': -200
        },
        {
            'callsign': 'DAL789', 'latitude': 40.6000, 'longitude': -74.1000,
            'baro_altitude': 25000, 'velocity': 380, 'true_track': 45, 'vertical_rate': 500
        }
    ])
    
    detector = RealTimeConflictDetector()
    conflicts = detector.detect_conflicts(sample_flights)
    
    print(f"Detected {len(conflicts)} potential conflicts:")
    for conflict in conflicts:
        print(f"- {conflict.aircraft_1} vs {conflict.aircraft_2}: "
              f"{conflict.risk_level} risk ({conflict.conflict_probability:.2%})")
    
    return conflicts

if __name__ == "__main__":
    test_conflict_detection()