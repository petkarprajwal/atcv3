"""
OpenSky Network API Integration Examples

This module provides comprehensive examples for using the OpenSky Network API
integration in various real-world scenarios including real-time tracking,
historical analysis, airport monitoring, and data visualization.
"""

import asyncio
import time
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import List, Dict, Optional

from config.opensky_config import OpenSkyConfig
from services.opensky_service import OpenSkyService
from models.opensky_models import StateVector, OpenSkyStates, FlightData, BoundingBox
from utils.opensky_utils import OpenSkyUtils


class OpenSkyExamples:
    """Collection of OpenSky API usage examples"""
    
    def __init__(self):
        """Initialize OpenSky service with configuration"""
        self.config = OpenSkyConfig()
        self.config.load_credentials()
        self.service = OpenSkyService(self.config)
    
    async def example_1_real_time_tracking(self):
        """
        Example 1: Real-time aircraft tracking
        
        This example demonstrates how to:
        - Get current aircraft states
        - Filter by geographic area
        - Track specific aircraft
        - Display real-time updates
        """
        print("=== Example 1: Real-time Aircraft Tracking ===")
        
        try:
            # Define area of interest (e.g., around New York)
            ny_bbox = BoundingBox(
                lat_min=40.0,
                lat_max=41.0,
                lon_min=-75.0,
                lon_max=-73.0
            )
            
            print(f"Tracking aircraft in New York area...")
            
            # Get current states in the area
            states = await self.service.get_states(bbox=ny_bbox, extended=True)
            
            print(f"Found {len(states.states)} aircraft in the area")
            print(f"Data timestamp: {datetime.fromtimestamp(states.time)}")
            
            # Display aircraft information
            for i, aircraft in enumerate(states.states[:5]):  # Show first 5
                print(f"\\nAircraft {i+1}:")
                print(f"  ICAO24: {aircraft.icao24}")
                print(f"  Callsign: {aircraft.callsign}")
                print(f"  Country: {aircraft.origin_country}")
                print(f"  Position: {aircraft.latitude:.4f}, {aircraft.longitude:.4f}")
                print(f"  Altitude: {aircraft.baro_altitude} m")
                print(f"  Velocity: {aircraft.velocity} m/s")
                print(f"  Heading: {aircraft.true_track}°")
                print(f"  On Ground: {aircraft.on_ground}")
            
            # Track a specific aircraft for multiple updates
            if states.states:
                target_aircraft = states.states[0]
                print(f"\\n--- Tracking {target_aircraft.callsign} ({target_aircraft.icao24}) ---")
                
                for update in range(3):
                    await asyncio.sleep(10)  # Wait 10 seconds
                    
                    # Get updated position
                    updated_states = await self.service.get_states(
                        icao24=[target_aircraft.icao24]
                    )
                    
                    if updated_states.states:
                        aircraft = updated_states.states[0]
                        print(f"Update {update + 1}: "
                              f"Pos: {aircraft.latitude:.4f}, {aircraft.longitude:.4f}, "
                              f"Alt: {aircraft.baro_altitude} m, "
                              f"Speed: {aircraft.velocity} m/s")
            
        except Exception as e:
            print(f"Error in real-time tracking: {e}")
    
    async def example_2_historical_analysis(self):
        """
        Example 2: Historical flight analysis
        
        This example demonstrates how to:
        - Retrieve historical flight data
        - Analyze flight patterns
        - Calculate statistics
        - Generate reports
        """
        print("\\n=== Example 2: Historical Flight Analysis ===")
        
        try:
            # Analyze flights from the last 2 hours
            end_time = datetime.now()
            begin_time = end_time - timedelta(hours=2)
            
            print(f"Analyzing flights from {begin_time} to {end_time}")
            
            # Get all flights in time range
            flights = await self.service.get_flights(begin_time, end_time)
            
            print(f"Found {len(flights)} flights in the time period")
            
            if not flights:
                print("No flights found in the specified time range")
                return
            
            # Analyze departure airports
            departure_airports = {}
            arrival_airports = {}
            
            for flight in flights:
                if flight.est_departure_airport:
                    departure_airports[flight.est_departure_airport] = \\
                        departure_airports.get(flight.est_departure_airport, 0) + 1
                
                if flight.est_arrival_airport:
                    arrival_airports[flight.est_arrival_airport] = \\
                        arrival_airports.get(flight.est_arrival_airport, 0) + 1
            
            # Top departure airports
            print("\\nTop 10 Departure Airports:")
            sorted_departures = sorted(departure_airports.items(), 
                                     key=lambda x: x[1], reverse=True)
            for airport, count in sorted_departures[:10]:
                print(f"  {airport}: {count} flights")
            
            # Top arrival airports
            print("\\nTop 10 Arrival Airports:")
            sorted_arrivals = sorted(arrival_airports.items(), 
                                   key=lambda x: x[1], reverse=True)
            for airport, count in sorted_arrivals[:10]:
                print(f"  {airport}: {count} flights")
            
            # Analyze specific aircraft
            if flights:
                sample_flight = flights[0]
                icao24 = sample_flight.icao24
                
                print(f"\\n--- Detailed analysis for aircraft {icao24} ---")
                
                # Get all flights for this aircraft
                aircraft_flights = await self.service.get_flights_by_aircraft(
                    icao24, begin_time, end_time
                )
                
                print(f"Aircraft {icao24} had {len(aircraft_flights)} flights:")
                for flight in aircraft_flights:
                    flight_time = datetime.fromtimestamp(flight.first_seen)
                    print(f"  {flight_time}: {flight.est_departure_airport} -> "
                          f"{flight.est_arrival_airport} ({flight.callsign})")
            
        except Exception as e:
            print(f"Error in historical analysis: {e}")
    
    async def example_3_airport_monitoring(self):
        """
        Example 3: Airport traffic monitoring
        
        This example demonstrates how to:
        - Monitor aircraft around specific airports
        - Track arrivals and departures
        - Calculate airport traffic statistics
        - Detect patterns
        """
        print("\\n=== Example 3: Airport Traffic Monitoring ===")
        
        try:
            # Monitor JFK Airport (example coordinates)
            jfk_lat, jfk_lon = 40.6413, -73.7781
            monitoring_radius = 50  # km
            
            # Create bounding box around airport
            airport_bbox = OpenSkyUtils.create_bounding_box(
                jfk_lat, jfk_lon, monitoring_radius
            )
            
            print(f"Monitoring aircraft within {monitoring_radius} km of JFK Airport")
            print(f"Area: {airport_bbox.lat_min:.4f} to {airport_bbox.lat_max:.4f} lat, "
                  f"{airport_bbox.lon_min:.4f} to {airport_bbox.lon_max:.4f} lon")
            
            # Get current aircraft in the area
            states = await self.service.get_states(bbox=airport_bbox)
            
            print(f"\\nFound {len(states.states)} aircraft in monitoring area")
            
            # Categorize aircraft by altitude and distance
            approaching = []
            departing = []
            cruising = []
            
            for aircraft in states.states:
                if aircraft.latitude and aircraft.longitude and aircraft.baro_altitude:
                    # Calculate distance from airport
                    distance = OpenSkyUtils.calculate_distance(
                        jfk_lat, jfk_lon, aircraft.latitude, aircraft.longitude
                    )
                    
                    # Categorize based on altitude and distance
                    if aircraft.baro_altitude < 3000 and distance < 20:
                        if aircraft.vertical_rate and aircraft.vertical_rate < -1:
                            approaching.append((aircraft, distance))
                        elif aircraft.vertical_rate and aircraft.vertical_rate > 1:
                            departing.append((aircraft, distance))
                    else:
                        cruising.append((aircraft, distance))
            
            print(f"\\nTraffic Analysis:")
            print(f"  Approaching aircraft: {len(approaching)}")
            print(f"  Departing aircraft: {len(departing)}")
            print(f"  Cruising aircraft: {len(cruising)}")
            
            # Show approaching aircraft details
            if approaching:
                print("\\nApproaching aircraft:")
                for aircraft, distance in sorted(approaching, key=lambda x: x[1]):
                    print(f"  {aircraft.callsign} ({aircraft.icao24}): "
                          f"{distance:.1f} km, {aircraft.baro_altitude} m, "
                          f"descending at {aircraft.vertical_rate:.1f} m/s")
            
            # Show departing aircraft details
            if departing:
                print("\\nDeparting aircraft:")
                for aircraft, distance in sorted(departing, key=lambda x: x[1]):
                    print(f"  {aircraft.callsign} ({aircraft.icao24}): "
                          f"{distance:.1f} km, {aircraft.baro_altitude} m, "
                          f"climbing at {aircraft.vertical_rate:.1f} m/s")
            
        except Exception as e:
            print(f"Error in airport monitoring: {e}")
    
    async def run_all_examples(self):
        """Run all examples in sequence"""
        print("OpenSky Network API Integration Examples")
        print("=" * 50)
        
        examples = [
            self.example_1_real_time_tracking,
            self.example_2_historical_analysis,
            self.example_3_airport_monitoring,
        ]
        
        for i, example in enumerate(examples, 1):
            try:
                await example()
                print(f"\\nExample {i} completed successfully!")
            except Exception as e:
                print(f"\\nExample {i} failed: {e}")
            
            if i < len(examples):
                print("\\n" + "-" * 50)
                await asyncio.sleep(5)  # Brief pause between examples
        
        print("\\nAll examples completed!")


async def main():
    """Main function to run examples"""
    examples = OpenSkyExamples()
    
    # Check if credentials are available
    if not examples.config.is_authenticated():
        print("Warning: No OpenSky credentials found in credentials.json")
        print("Some examples may fail without authentication.")
        print("Public API access is limited and rate-limited.")
        print()
    
    try:
        # Run individual examples or all examples
        print("Select an example to run:")
        print("1. Real-time aircraft tracking")
        print("2. Historical flight analysis")
        print("3. Airport traffic monitoring")
        print("4. Run all examples")
        
        choice = input("\\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            await examples.example_1_real_time_tracking()
        elif choice == "2":
            await examples.example_2_historical_analysis()
        elif choice == "3":
            await examples.example_3_airport_monitoring()
        elif choice == "4":
            await examples.run_all_examples()
        else:
            print("Invalid choice. Running real-time tracking example...")
            await examples.example_1_real_time_tracking()
    
    except KeyboardInterrupt:
        print("\\nExamples interrupted by user")
    except Exception as e:
        print(f"Error running examples: {e}")


if __name__ == "__main__":
    asyncio.run(main())
        
        try:
            # Get current aircraft states in the area
            states = self.service.get_current_states(bbox=ny_bbox)
            
            print(f"Found {states.aircraft_count} aircraft in New York area")
            
            # Filter for aircraft with position data
            positioned_aircraft = [s for s in states.states if s.has_position]
            print(f"{len(positioned_aircraft)} aircraft have position data")
            
            # Show some details
            for i, aircraft in enumerate(positioned_aircraft[:5]):  # Show first 5
                print(f"  {i+1}. {aircraft.callsign or 'N/A'} ({aircraft.icao24}) "
                      f"at {aircraft.latitude:.3f}, {aircraft.longitude:.3f}, "
                      f"{aircraft.baro_altitude or 0:.0f}m")
            
            # Convert to DataFrame for analysis
            df = states_to_dataframe(positioned_aircraft)
            
            return {
                'total_aircraft': states.aircraft_count,
                'positioned_aircraft': len(positioned_aircraft),
                'area': ny_bbox.dict(),
                'dataframe_shape': df.shape,
                'sample_data': df.head().to_dict('records') if not df.empty else []
            }
            
        except OpenSkyAPIException as e:
            print(f"API Error: {e}")
            return {'error': str(e)}
    
    def example_2_specific_aircraft_tracking(self, icao24: str = "a835af") -> Dict[str, Any]:
        """
        Example 2: Track a specific aircraft
        """
        print(f"\\n=== Example 2: Tracking specific aircraft {icao24} ===")
        
        try:
            # Get current state of specific aircraft
            states = self.service.get_current_states(icao24=icao24)
            
            if states.aircraft_count == 0:
                print(f"Aircraft {icao24} not currently visible")
                return {'aircraft_found': False}
            
            aircraft = states.states[0]
            print(f"Aircraft found: {aircraft.callsign or 'Unknown'}")
            print(f"Position: {aircraft.latitude}, {aircraft.longitude}")
            print(f"Altitude: {aircraft.baro_altitude}m")
            print(f"Speed: {aircraft.velocity}m/s")
            print(f"Country: {aircraft.origin_country}")
            
            # Get historical track (if available)
            try:
                track = self.service.get_aircraft_track(icao24)
                print(f"Track has {track.waypoint_count} waypoints")
                
                if track.waypoints:
                    stats = calculate_track_statistics(track.waypoints)
                    print(f"Track statistics: {stats}")
                
                return {
                    'aircraft_found': True,
                    'current_state': aircraft.dict(),
                    'track_waypoints': track.waypoint_count,
                    'track_stats': stats if track.waypoints else None
                }
                
            except OpenSkyAPIException as track_error:
                print(f"Could not get track: {track_error}")
                return {
                    'aircraft_found': True,
                    'current_state': aircraft.dict(),
                    'track_error': str(track_error)
                }
            
        except OpenSkyAPIException as e:
            print(f"API Error: {e}")
            return {'error': str(e)}
    
    def example_3_airport_traffic_monitoring(self, airport_icao: str = "KJFK") -> Dict[str, Any]:
        """
        Example 3: Monitor airport traffic (arrivals and departures)
        """
        print(f"\\n=== Example 3: Airport traffic monitoring for {airport_icao} ===")
        
        # Get data for last 24 hours
        end_time = int(time.time())
        start_time = end_time - 86400  # 24 hours ago
        
        try:
            # Get arrivals and departures
            arrivals = self.service.get_airport_arrivals(airport_icao, start_time, end_time)
            departures = self.service.get_airport_departures(airport_icao, start_time, end_time)
            
            print(f"Arrivals in last 24h: {len(arrivals)}")
            print(f"Departures in last 24h: {len(departures)}")
            
            # Show some examples
            if arrivals:
                print("\\nSample arrivals:")
                for i, flight in enumerate(arrivals[:3]):
                    print(f"  {i+1}. {flight.callsign or 'N/A'} from {flight.est_departure_airport or 'Unknown'}")
            
            if departures:
                print("\\nSample departures:")
                for i, flight in enumerate(departures[:3]):
                    print(f"  {i+1}. {flight.callsign or 'N/A'} to {flight.est_arrival_airport or 'Unknown'}")
            
            # Convert to DataFrames
            arrivals_df = flights_to_dataframe(arrivals) if arrivals else pd.DataFrame()
            departures_df = flights_to_dataframe(departures) if departures else pd.DataFrame()
            
            return {
                'airport': airport_icao,
                'period_hours': 24,
                'arrivals_count': len(arrivals),
                'departures_count': len(departures),
                'arrivals_data': arrivals_df.head().to_dict('records') if not arrivals_df.empty else [],
                'departures_data': departures_df.head().to_dict('records') if not departures_df.empty else []
            }
            
        except OpenSkyAPIException as e:
            print(f"API Error: {e}")
            return {'error': str(e)}
    
    def example_4_multi_aircraft_comparison(self, icao24_list: List[str]) -> Dict[str, Any]:
        """
        Example 4: Compare multiple aircraft
        """
        print(f"\\n=== Example 4: Multi-aircraft comparison ===")
        
        try:
            # Get states for multiple aircraft
            states = self.service.get_current_states(icao24=icao24_list)
            
            comparison_data = []
            for aircraft in states.states:
                if aircraft.has_position:
                    comparison_data.append({
                        'icao24': aircraft.icao24,
                        'callsign': aircraft.callsign,
                        'country': aircraft.origin_country,
                        'altitude': aircraft.baro_altitude,
                        'speed': aircraft.velocity,
                        'latitude': aircraft.latitude,
                        'longitude': aircraft.longitude
                    })
            
            print(f"Found {len(comparison_data)} aircraft with position data")
            
            # Create comparison DataFrame
            df = pd.DataFrame(comparison_data)
            
            if not df.empty:
                print("\\nComparison summary:")
                print(f"Average altitude: {df['altitude'].mean():.0f}m")
                print(f"Average speed: {df['speed'].mean():.1f}m/s")
                print(f"Countries represented: {df['country'].nunique()}")
            
            return {
                'requested_aircraft': len(icao24_list),
                'found_aircraft': len(comparison_data),
                'comparison_data': comparison_data,
                'summary_stats': df.describe().to_dict() if not df.empty else {}
            }
            
        except OpenSkyAPIException as e:
            print(f"API Error: {e}")
            return {'error': str(e)}
    
    def example_5_distance_based_filtering(self, center_lat: float = 40.7128, 
                                          center_lon: float = -74.0060, 
                                          radius_km: float = 100) -> Dict[str, Any]:
        """
        Example 5: Filter aircraft by distance from a point
        """
        print(f"\\n=== Example 5: Distance-based filtering ===")
        print(f"Center: {center_lat}, {center_lon}")
        print(f"Radius: {radius_km} km")
        
        # Create bounding box for initial filtering
        bbox = create_bounding_box(center_lat, center_lon, radius_km * 1.5)  # Wider initial filter
        
        try:
            # Get aircraft in general area
            states = self.service.get_current_states(bbox=bbox)
            print(f"Found {states.aircraft_count} aircraft in bounding box")
            
            # Filter by exact distance
            positioned_aircraft = [s for s in states.states if s.has_position]
            nearby_aircraft = filter_states_by_distance(
                positioned_aircraft, center_lat, center_lon, radius_km
            )
            
            print(f"Found {len(nearby_aircraft)} aircraft within {radius_km}km")
            
            # Calculate distances
            distance_data = []
            for aircraft in nearby_aircraft:
                from utils.opensky_utils import haversine_distance
                distance = haversine_distance(
                    center_lat, center_lon,
                    aircraft.latitude, aircraft.longitude
                )
                distance_data.append({
                    'icao24': aircraft.icao24,
                    'callsign': aircraft.callsign,
                    'distance_km': round(distance, 2),
                    'altitude': aircraft.baro_altitude
                })
            
            # Sort by distance
            distance_data.sort(key=lambda x: x['distance_km'])
            
            print("\\nClosest aircraft:")
            for i, aircraft in enumerate(distance_data[:5]):
                print(f"  {i+1}. {aircraft['callsign'] or 'N/A'} - {aircraft['distance_km']}km away")
            
            return {
                'center_point': {'lat': center_lat, 'lon': center_lon},
                'radius_km': radius_km,
                'total_in_bbox': states.aircraft_count,
                'within_radius': len(nearby_aircraft),
                'closest_aircraft': distance_data
            }
            
        except OpenSkyAPIException as e:
            print(f"API Error: {e}")
            return {'error': str(e)}
    
    def example_6_historical_analysis(self, icao24: str = "a835af") -> Dict[str, Any]:
        """
        Example 6: Historical flight analysis
        """
        print(f"\\n=== Example 6: Historical analysis for {icao24} ===")
        
        # Analyze last 7 days
        end_time = int(time.time())
        start_time = end_time - (7 * 24 * 3600)  # 7 days ago
        
        try:
            flights = self.service.get_aircraft_flights(icao24, start_time, end_time)
            print(f"Found {len(flights)} flights in last 7 days")
            
            if not flights:
                return {'flights_found': 0}
            
            # Analyze flight patterns
            analysis = {
                'total_flights': len(flights),
                'unique_departures': len(set(f.est_departure_airport for f in flights if f.est_departure_airport)),
                'unique_arrivals': len(set(f.est_arrival_airport for f in flights if f.est_arrival_airport)),
                'avg_flight_duration': sum(f.flight_duration_seconds for f in flights) / len(flights),
                'flight_details': []
            }
            
            # Get details for each flight
            for flight in flights:
                analysis['flight_details'].append({
                    'callsign': flight.callsign,
                    'departure': flight.est_departure_airport,
                    'arrival': flight.est_arrival_airport,
                    'duration_hours': flight.flight_duration_seconds / 3600,
                    'departure_time': flight.departure_datetime.isoformat(),
                    'arrival_time': flight.arrival_datetime.isoformat()
                })
            
            print(f"Average flight duration: {analysis['avg_flight_duration']/3600:.1f} hours")
            print(f"Unique departure airports: {analysis['unique_departures']}")
            print(f"Unique arrival airports: {analysis['unique_arrivals']}")
            
            return analysis
            
        except OpenSkyAPIException as e:
            print(f"API Error: {e}")
            return {'error': str(e)}
    
    def example_7_export_data(self, output_dir: str = "opensky_exports") -> Dict[str, Any]:
        """
        Example 7: Export data for visualization and analysis
        """
        print(f"\\n=== Example 7: Data export ===")
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        try:
            # Get current states for a large area (Europe)
            europe_bbox = BoundingBox(
                min_latitude=35.0,
                max_latitude=70.0,
                min_longitude=-10.0,
                max_longitude=40.0
            )
            
            states = self.service.get_current_states(bbox=europe_bbox)
            print(f"Retrieved {states.aircraft_count} aircraft over Europe")
            
            # Convert to DataFrame
            positioned_aircraft = [s for s in states.states if s.has_position]
            df = states_to_dataframe(positioned_aircraft)
            
            if df.empty:
                return {'exported_files': 0, 'error': 'No data to export'}
            
            # Export to different formats
            exports = {}
            
            # CSV export
            csv_file = output_path / f"aircraft_states_{int(time.time())}.csv"
            df.to_csv(csv_file, index=False)
            exports['csv'] = str(csv_file)
            
            # JSON export
            json_file = output_path / f"aircraft_states_{int(time.time())}.json"
            df.to_json(json_file, orient='records', indent=2)
            exports['json'] = str(json_file)
            
            # Excel export (if openpyxl available)
            try:
                excel_file = output_path / f"aircraft_states_{int(time.time())}.xlsx"
                df.to_excel(excel_file, index=False)
                exports['excel'] = str(excel_file)
            except ImportError:
                print("openpyxl not available, skipping Excel export")
            
            print(f"Exported data to {len(exports)} formats")
            for format_type, file_path in exports.items():
                print(f"  {format_type.upper()}: {file_path}")
            
            return {
                'aircraft_count': len(positioned_aircraft),
                'exported_files': len(exports),
                'file_paths': exports,
                'data_sample': df.head().to_dict('records')
            }
            
        except OpenSkyAPIException as e:
            print(f"API Error: {e}")
            return {'error': str(e)}
    
    def run_all_examples(self) -> Dict[str, Any]:
        """
        Run all examples and return combined results
        """
        print("\\n" + "="*60)
        print("RUNNING ALL OPENSKY API EXAMPLES")
        print("="*60)
        
        results = {}
        
        # Example 1: Real-time area tracking
        results['area_tracking'] = self.example_1_real_time_tracking_area()
        
        # Example 2: Specific aircraft (using common US aircraft)
        results['specific_aircraft'] = self.example_2_specific_aircraft_tracking("a835af")
        
        # Example 3: Airport monitoring
        results['airport_monitoring'] = self.example_3_airport_traffic_monitoring("KJFK")
        
        # Example 4: Multi-aircraft comparison
        sample_aircraft = ["a835af", "a0f842", "a1c2fd"]  # Sample US aircraft
        results['multi_aircraft'] = self.example_4_multi_aircraft_comparison(sample_aircraft)
        
        # Example 5: Distance filtering (NYC area)
        results['distance_filtering'] = self.example_5_distance_based_filtering()
        
        # Example 6: Historical analysis
        results['historical_analysis'] = self.example_6_historical_analysis("a835af")
        
        # Example 7: Data export
        results['data_export'] = self.example_7_export_data()
        
        print("\\n" + "="*60)
        print("ALL EXAMPLES COMPLETED")
        print("="*60)
        
        return results
    
    def close(self):
        """Close the OpenSky service"""
        self.service.close()


def main():
    """
    Main function to run examples
    """
    examples = OpenSkyExamples()
    
    try:
        # Run all examples
        results = examples.run_all_examples()
        
        # Print summary
        print("\\n\\nEXECUTION SUMMARY:")
        print("-" * 40)
        for example_name, result in results.items():
            status = "ERROR" if 'error' in result else "SUCCESS"
            print(f"{example_name}: {status}")
        
        return results
        
    finally:
        examples.close()


if __name__ == "__main__":
    main()