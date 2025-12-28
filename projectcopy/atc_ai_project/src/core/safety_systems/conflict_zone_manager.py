#!/usr/bin/env python3
"""
Conflict Zone Manager
Dynamic airspace restriction and conflict zone management system
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
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union
import geopandas as gpd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ConflictZone:
    """Conflict zone data structure"""
    zone_id: str
    name: str
    zone_type: str  # "warzone", "military", "restricted", "temporary", "emergency"
    status: str  # "active", "inactive", "scheduled", "expired"
    geometry: Dict[str, Any]  # GeoJSON geometry
    altitude_min: float
    altitude_max: float
    start_time: datetime
    end_time: Optional[datetime]
    severity: str  # "low", "medium", "high", "critical"
    description: str
    source: str  # "military", "government", "notam", "manual"
    last_updated: datetime

@dataclass
class FlightRestriction:
    """Flight restriction data structure"""
    restriction_id: str
    zone_id: str
    restriction_type: str  # "no_fly", "restricted", "caution", "advisory"
    aircraft_types: List[str]  # ["commercial", "military", "general_aviation"]
    altitude_restrictions: Dict[str, float]
    time_restrictions: Dict[str, Any]
    exceptions: List[str]
    enforcement_level: str  # "mandatory", "advisory", "recommended"

@dataclass
class RouteImpact:
    """Route impact assessment"""
    route_id: str
    aircraft_id: str
    impact_level: str  # "none", "minor", "moderate", "severe", "blocked"
    affected_segments: List[Dict[str, Any]]
    alternative_routes: List[Dict[str, Any]]
    estimated_delay: float  # minutes
    fuel_impact: float  # percentage
    safety_risk: str  # "low", "medium", "high", "critical"

class ConflictZoneManager:
    """Advanced conflict zone management system"""
    
    def __init__(self):
        # Conflict zone database
        self.conflict_zones: Dict[str, ConflictZone] = {}
        self.flight_restrictions: Dict[str, FlightRestriction] = {}
        
        # Zone types and their characteristics
        self.zone_types = {
            "warzone": {
                "severity": "critical",
                "enforcement": "mandatory",
                "altitude_range": (0, 60000),
                "update_frequency": 300  # 5 minutes
            },
            "military": {
                "severity": "high",
                "enforcement": "mandatory",
                "altitude_range": (0, 50000),
                "update_frequency": 600  # 10 minutes
            },
            "restricted": {
                "severity": "medium",
                "enforcement": "advisory",
                "altitude_range": (0, 40000),
                "update_frequency": 1800  # 30 minutes
            },
            "temporary": {
                "severity": "medium",
                "enforcement": "advisory",
                "altitude_range": (0, 30000),
                "update_frequency": 900  # 15 minutes
            },
            "emergency": {
                "severity": "critical",
                "enforcement": "mandatory",
                "altitude_range": (0, 60000),
                "update_frequency": 60  # 1 minute
            }
        }
        
        # Data sources for conflict zones
        self.data_sources = {
            "military": "https://api.military-zones.gov/active",
            "notam": "https://api.faa.gov/notam/restrictions",
            "government": "https://api.gov/airspace/restrictions",
            "manual": "internal_database"
        }
        
        # Performance metrics
        self.zones_processed = 0
        self.restrictions_applied = 0
        self.routes_impacted = 0
        
        logger.info("Conflict Zone Manager initialized")
    
    def load_conflict_zones(self, source: str = "all") -> bool:
        """Load conflict zones from data sources"""
        
        try:
            if source == "all":
                for source_name in self.data_sources:
                    self._load_from_source(source_name)
            else:
                self._load_from_source(source)
            
            logger.info(f"Loaded {len(self.conflict_zones)} conflict zones")
            return True
            
        except Exception as e:
            logger.error(f"Error loading conflict zones: {e}")
            return False
    
    def _load_from_source(self, source: str):
        """Load conflict zones from specific source"""
        
        if source == "manual":
            self._load_manual_zones()
        else:
            # For external sources, we'll simulate the data
            self._load_simulated_zones(source)
    
    def _load_manual_zones(self):
        """Load manually defined conflict zones"""
        
        # Example warzone (Ukraine conflict)
        ukraine_zone = ConflictZone(
            zone_id="WAR_UKR_001",
            name="Ukraine Conflict Zone",
            zone_type="warzone",
            status="active",
            geometry={
                "type": "Polygon",
                "coordinates": [[
                    [22.0, 45.0], [40.0, 45.0], [40.0, 52.0], [22.0, 52.0], [22.0, 45.0]
                ]]
            },
            altitude_min=0,
            altitude_max=60000,
            start_time=datetime(2022, 2, 24),
            end_time=None,
            severity="critical",
            description="Active conflict zone - all civilian flights prohibited",
            source="manual",
            last_updated=datetime.now()
        )
        
        self.conflict_zones[ukraine_zone.zone_id] = ukraine_zone
        
        # Example military operation area
        military_zone = ConflictZone(
            zone_id="MIL_USA_001",
            name="Nevada Test Range",
            zone_type="military",
            status="active",
            geometry={
                "type": "Polygon",
                "coordinates": [[
                    [-117.0, 36.0], [-115.0, 36.0], [-115.0, 38.0], [-117.0, 38.0], [-117.0, 36.0]
                ]]
            },
            altitude_min=0,
            altitude_max=50000,
            start_time=datetime.now() - timedelta(days=1),
            end_time=datetime.now() + timedelta(days=7),
            severity="high",
            description="Military training operations - restricted airspace",
            source="manual",
            last_updated=datetime.now()
        )
        
        self.conflict_zones[military_zone.zone_id] = military_zone
    
    def _load_simulated_zones(self, source: str):
        """Load simulated conflict zones for testing"""
        
        # Simulate different types of zones
        if source == "military":
            # Add simulated military zones
            for i in range(3):
                zone = ConflictZone(
                    zone_id=f"MIL_SIM_{i+1:03d}",
                    name=f"Military Zone {i+1}",
                    zone_type="military",
                    status="active",
                    geometry={
                        "type": "Polygon",
                        "coordinates": [[
                            [-120 + i*2, 35 + i], [-118 + i*2, 35 + i],
                            [-118 + i*2, 37 + i], [-120 + i*2, 37 + i],
                            [-120 + i*2, 35 + i]
                        ]]
                    },
                    altitude_min=0,
                    altitude_max=50000,
                    start_time=datetime.now(),
                    end_time=datetime.now() + timedelta(days=30),
                    severity="high",
                    description=f"Simulated military zone {i+1}",
                    source=source,
                    last_updated=datetime.now()
                )
                self.conflict_zones[zone.zone_id] = zone
        
        elif source == "notam":
            # Add simulated NOTAM restrictions
            for i in range(2):
                zone = ConflictZone(
                    zone_id=f"NOTAM_SIM_{i+1:03d}",
                    name=f"NOTAM Restriction {i+1}",
                    zone_type="temporary",
                    status="active",
                    geometry={
                        "type": "Polygon",
                        "coordinates": [[
                            [-80 + i*5, 25 + i], [-75 + i*5, 25 + i],
                            [-75 + i*5, 30 + i], [-80 + i*5, 30 + i],
                            [-80 + i*5, 25 + i]
                        ]]
                    },
                    altitude_min=0,
                    altitude_max=30000,
                    start_time=datetime.now(),
                    end_time=datetime.now() + timedelta(days=7),
                    severity="medium",
                    description=f"Simulated NOTAM restriction {i+1}",
                    source=source,
                    last_updated=datetime.now()
                )
                self.conflict_zones[zone.zone_id] = zone
    
    def check_aircraft_in_conflict_zone(self, aircraft_lat: float, aircraft_lon: float, 
                                      aircraft_alt: float) -> List[ConflictZone]:
        """Check if aircraft is in any conflict zone"""
        
        conflicting_zones = []
        
        for zone in self.conflict_zones.values():
            if zone.status != "active":
                continue
            
            # Check altitude range
            if not (zone.altitude_min <= aircraft_alt <= zone.altitude_max):
                continue
            
            # Check if point is within zone geometry
            if self._point_in_zone(aircraft_lat, aircraft_lon, zone.geometry):
                conflicting_zones.append(zone)
        
        return conflicting_zones
    
    def _point_in_zone(self, lat: float, lon: float, geometry: Dict[str, Any]) -> bool:
        """Check if point is within zone geometry"""
        
        try:
            if geometry["type"] == "Polygon":
                coords = geometry["coordinates"][0]  # Exterior ring
                
                # Simple point-in-polygon test
                x, y = lon, lat
                n = len(coords)
                inside = False
                
                p1x, p1y = coords[0]
                for i in range(1, n + 1):
                    p2x, p2y = coords[i % n]
                    if y > min(p1y, p2y):
                        if y <= max(p1y, p2y):
                            if x <= max(p1x, p2x):
                                if p1y != p2y:
                                    xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                                if p1x == p2x or x <= xinters:
                                    inside = not inside
                    p1x, p1y = p2x, p2y
                
                return inside
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking point in zone: {e}")
            return False
    
    def assess_route_impact(self, route_coordinates: List[Tuple[float, float]], 
                          route_altitudes: List[float]) -> RouteImpact:
        """Assess impact of conflict zones on a route"""
        
        route_id = f"ROUTE_{int(datetime.now().timestamp())}"
        affected_segments = []
        alternative_routes = []
        max_impact_level = "none"
        total_delay = 0
        fuel_impact = 0
        
        # Check each segment of the route
        for i in range(len(route_coordinates) - 1):
            start_lat, start_lon = route_coordinates[i]
            end_lat, end_lon = route_coordinates[i + 1]
            start_alt = route_altitudes[i] if i < len(route_altitudes) else route_altitudes[0]
            end_alt = route_altitudes[i + 1] if i + 1 < len(route_altitudes) else route_altitudes[-1]
            
            # Check if segment intersects with any conflict zones
            segment_impact = self._assess_segment_impact(
                start_lat, start_lon, start_alt,
                end_lat, end_lon, end_alt
            )
            
            if segment_impact["impact_level"] != "none":
                affected_segments.append({
                    "segment_id": i,
                    "start": (start_lat, start_lon, start_alt),
                    "end": (end_lat, end_lon, end_alt),
                    "impact_level": segment_impact["impact_level"],
                    "conflicting_zones": segment_impact["zones"],
                    "estimated_delay": segment_impact["delay"]
                })
                
                # Update overall impact
                if segment_impact["impact_level"] in ["severe", "blocked"]:
                    max_impact_level = "severe"
                elif segment_impact["impact_level"] == "moderate" and max_impact_level != "severe":
                    max_impact_level = "moderate"
                elif segment_impact["impact_level"] == "minor" and max_impact_level not in ["severe", "moderate"]:
                    max_impact_level = "minor"
                
                total_delay += segment_impact["delay"]
                fuel_impact += segment_impact["fuel_impact"]
        
        # Generate alternative routes if needed
        if max_impact_level in ["severe", "blocked"]:
            alternative_routes = self._generate_alternative_routes(route_coordinates, route_altitudes)
        
        # Determine safety risk
        safety_risk = self._determine_safety_risk(max_impact_level, affected_segments)
        
        return RouteImpact(
            route_id=route_id,
            aircraft_id="UNKNOWN",
            impact_level=max_impact_level,
            affected_segments=affected_segments,
            alternative_routes=alternative_routes,
            estimated_delay=total_delay,
            fuel_impact=fuel_impact,
            safety_risk=safety_risk
        )
    
    def _assess_segment_impact(self, start_lat: float, start_lon: float, start_alt: float,
                             end_lat: float, end_lon: float, end_alt: float) -> Dict[str, Any]:
        """Assess impact of conflict zones on a route segment"""
        
        conflicting_zones = []
        max_severity = "low"
        total_delay = 0
        fuel_impact = 0
        
        # Check multiple points along the segment
        num_points = 10
        for i in range(num_points + 1):
            t = i / num_points
            lat = start_lat + t * (end_lat - start_lat)
            lon = start_lon + t * (end_lon - start_lon)
            alt = start_alt + t * (end_alt - start_alt)
            
            # Check for conflict zones
            zones = self.check_aircraft_in_conflict_zone(lat, lon, alt)
            for zone in zones:
                if zone not in conflicting_zones:
                    conflicting_zones.append(zone)
                    
                    # Update severity
                    if zone.severity == "critical":
                        max_severity = "critical"
                    elif zone.severity == "high" and max_severity not in ["critical"]:
                        max_severity = "high"
                    elif zone.severity == "medium" and max_severity not in ["critical", "high"]:
                        max_severity = "medium"
        
        # Calculate impact based on severity
        if max_severity == "critical":
            impact_level = "blocked"
            total_delay = 60  # 1 hour delay
            fuel_impact = 15  # 15% fuel impact
        elif max_severity == "high":
            impact_level = "severe"
            total_delay = 30  # 30 minutes delay
            fuel_impact = 10  # 10% fuel impact
        elif max_severity == "medium":
            impact_level = "moderate"
            total_delay = 15  # 15 minutes delay
            fuel_impact = 5   # 5% fuel impact
        elif max_severity == "low":
            impact_level = "minor"
            total_delay = 5   # 5 minutes delay
            fuel_impact = 2   # 2% fuel impact
        else:
            impact_level = "none"
            total_delay = 0
            fuel_impact = 0
        
        return {
            "impact_level": impact_level,
            "zones": [zone.zone_id for zone in conflicting_zones],
            "delay": total_delay,
            "fuel_impact": fuel_impact
        }
    
    def _generate_alternative_routes(self, original_route: List[Tuple[float, float]], 
                                   altitudes: List[float]) -> List[Dict[str, Any]]:
        """Generate alternative routes to avoid conflict zones"""
        
        alternatives = []
        
        # Simple alternative: offset route by fixed distance
        offset_distance = 0.5  # degrees
        
        # Generate 4 alternative routes (north, south, east, west)
        directions = [
            ("north", (0, offset_distance)),
            ("south", (0, -offset_distance)),
            ("east", (offset_distance, 0)),
            ("west", (-offset_distance, 0))
        ]
        
        for direction, (lat_offset, lon_offset) in directions:
            alt_route = []
            for lat, lon in original_route:
                alt_route.append((lat + lat_offset, lon + lon_offset))
            
            # Assess impact of alternative route
            impact = self.assess_route_impact(alt_route, altitudes)
            
            alternatives.append({
                "direction": direction,
                "coordinates": alt_route,
                "impact_level": impact.impact_level,
                "estimated_delay": impact.estimated_delay,
                "fuel_impact": impact.fuel_impact,
                "safety_risk": impact.safety_risk
            })
        
        return alternatives
    
    def _determine_safety_risk(self, impact_level: str, affected_segments: List[Dict[str, Any]]) -> str:
        """Determine overall safety risk"""
        
        if impact_level == "blocked":
            return "critical"
        elif impact_level == "severe":
            return "high"
        elif impact_level == "moderate":
            return "medium"
        elif impact_level == "minor":
            return "low"
        else:
            return "low"
    
    def add_conflict_zone(self, zone: ConflictZone) -> bool:
        """Add new conflict zone"""
        
        try:
            self.conflict_zones[zone.zone_id] = zone
            logger.info(f"Added conflict zone: {zone.zone_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding conflict zone: {e}")
            return False
    
    def update_conflict_zone(self, zone_id: str, updates: Dict[str, Any]) -> bool:
        """Update existing conflict zone"""
        
        if zone_id not in self.conflict_zones:
            logger.warning(f"Conflict zone not found: {zone_id}")
            return False
        
        try:
            zone = self.conflict_zones[zone_id]
            for key, value in updates.items():
                if hasattr(zone, key):
                    setattr(zone, key, value)
            
            zone.last_updated = datetime.now()
            logger.info(f"Updated conflict zone: {zone_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating conflict zone: {e}")
            return False
    
    def remove_conflict_zone(self, zone_id: str) -> bool:
        """Remove conflict zone"""
        
        if zone_id not in self.conflict_zones:
            logger.warning(f"Conflict zone not found: {zone_id}")
            return False
        
        try:
            del self.conflict_zones[zone_id]
            logger.info(f"Removed conflict zone: {zone_id}")
            return True
        except Exception as e:
            logger.error(f"Error removing conflict zone: {e}")
            return False
    
    def get_active_zones(self) -> List[ConflictZone]:
        """Get all active conflict zones"""
        
        return [zone for zone in self.conflict_zones.values() if zone.status == "active"]
    
    def get_zones_by_type(self, zone_type: str) -> List[ConflictZone]:
        """Get conflict zones by type"""
        
        return [zone for zone in self.conflict_zones.values() if zone.zone_type == zone_type]
    
    def get_zones_by_severity(self, severity: str) -> List[ConflictZone]:
        """Get conflict zones by severity"""
        
        return [zone for zone in self.conflict_zones.values() if zone.severity == severity]
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get conflict zone manager status"""
        
        active_zones = self.get_active_zones()
        zone_types = {}
        severities = {}
        
        for zone in active_zones:
            zone_types[zone.zone_type] = zone_types.get(zone.zone_type, 0) + 1
            severities[zone.severity] = severities.get(zone.severity, 0) + 1
        
        return {
            "system_status": "operational",
            "total_zones": len(self.conflict_zones),
            "active_zones": len(active_zones),
            "zone_types": zone_types,
            "severities": severities,
            "zones_processed": self.zones_processed,
            "restrictions_applied": self.restrictions_applied,
            "routes_impacted": self.routes_impacted,
            "last_update": datetime.now().isoformat()
        }

def main():
    """Test the conflict zone manager"""
    
    # Initialize conflict zone manager
    manager = ConflictZoneManager()
    
    # Load conflict zones
    manager.load_conflict_zones()
    
    # Test aircraft position
    test_lat, test_lon, test_alt = 40.7128, -74.0060, 35000
    
    # Check for conflicts
    conflicting_zones = manager.check_aircraft_in_conflict_zone(test_lat, test_lon, test_alt)
    
    print(f"Aircraft at ({test_lat}, {test_lon}, {test_alt})")
    print(f"Conflicting zones: {len(conflicting_zones)}")
    
    for zone in conflicting_zones:
        print(f"Zone: {zone.name} ({zone.zone_type}) - Severity: {zone.severity}")
    
    # Test route impact
    test_route = [
        (40.7128, -74.0060),  # New York
        (40.6892, -74.0445),  # Statue of Liberty
        (40.7589, -73.9851)   # Times Square
    ]
    test_altitudes = [35000, 35000, 35000]
    
    impact = manager.assess_route_impact(test_route, test_altitudes)
    
    print(f"\nRoute Impact Assessment:")
    print(f"Impact Level: {impact.impact_level}")
    print(f"Affected Segments: {len(impact.affected_segments)}")
    print(f"Estimated Delay: {impact.estimated_delay} minutes")
    print(f"Fuel Impact: {impact.fuel_impact}%")
    print(f"Safety Risk: {impact.safety_risk}")
    
    # Get system status
    status = manager.get_system_status()
    print(f"\nSystem Status:")
    print(f"Active Zones: {status['active_zones']}")
    print(f"Zone Types: {status['zone_types']}")

if __name__ == "__main__":
    main()



