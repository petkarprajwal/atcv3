# OpenSky Network API Integration Documentation

## Overview

This comprehensive integration provides a production-ready wrapper for the OpenSky Network API, designed specifically for Air Traffic Control applications. The integration includes secure credential management, rate limiting, caching, error handling, and extensive data validation.

## Features

- **Secure Credential Management**: Loads credentials from `credentials.json` with environment-based configuration
- **Rate Limiting**: Respects OpenSky API limits (10s for unauthenticated, faster for authenticated users)
- **Intelligent Caching**: TTL-based caching to minimize API calls and improve performance
- **Comprehensive Error Handling**: Handles all API error scenarios gracefully
- **Data Validation**: Full Pydantic models for type safety and validation
- **Utility Functions**: Helper functions for common operations
- **Async Support**: Full async/await support for modern applications
- **Testing Suite**: Comprehensive tests including mocks and integration tests

## Quick Start

### 1. Setup Credentials

Create `credentials.json` in your project root:

```json
{
  "opensky": {
    "username": "your_username",
    "password": "your_password"
  }
}
```

### 2. Basic Usage

```python
import asyncio
from services.opensky_service import OpenSkyService
from models.opensky_models import BoundingBox

async def main():
    # Initialize service (automatically loads credentials)
    service = OpenSkyService()

    # Get aircraft in a specific area
    bbox = BoundingBox(
        lat_min=40.0,
        lat_max=41.0,
        lon_min=-74.0,
        lon_max=-73.0
    )

    states = await service.get_states(bbox=bbox)
    print(f"Found {len(states.states)} aircraft")

    # Track specific aircraft
    aircraft_states = await service.get_states(icao24=["a835af"])

    # Get historical flights
    from datetime import datetime, timedelta
    end_time = datetime.now()
    begin_time = end_time - timedelta(hours=1)
    flights = await service.get_flights(begin_time, end_time)

asyncio.run(main())
```

## API Reference

### OpenSkyService

The main service class for interacting with the OpenSky Network API.

#### Initialization

```python
service = OpenSkyService(config=None)
```

- `config`: Optional OpenSkyConfig instance (uses default config if None)

#### Real-time Data Methods

##### get_states()

```python
async def get_states(bbox=None, icao24=None, extended=False) -> OpenSkyStates
```

Retrieve current aircraft states.

**Parameters:**
- `bbox` (BoundingBox, optional): Geographic area filter
- `icao24` (List[str], optional): Specific aircraft ICAO24 addresses
- `extended` (bool): Request extended data (requires authentication)

**Returns:** OpenSkyStates object with aircraft data

**Example:**
```python
# All aircraft
states = await service.get_states()

# Aircraft in NYC area
ny_bbox = BoundingBox(lat_min=40.0, lat_max=41.0, 
                      lon_min=-74.5, lon_max=-73.0)
states = await service.get_states(bbox=ny_bbox)

# Specific aircraft
states = await service.get_states(icao24=["a835af", "abc123"])
```

##### get_flights()

```python
async def get_flights(begin_time, end_time) -> List[FlightData]
```

Retrieve flights within a time range.

**Parameters:**
- `begin_time` (datetime): Start time
- `end_time` (datetime): End time (max 2 hours from begin_time)

**Returns:** List of FlightData objects

**Example:**
```python
from datetime import datetime, timedelta

end_time = datetime.now()
begin_time = end_time - timedelta(hours=1)
flights = await service.get_flights(begin_time, end_time)
```

##### get_flights_by_aircraft()

```python
async def get_flights_by_aircraft(icao24, begin_time, end_time) -> List[FlightData]
```

Get historical flights for a specific aircraft.

**Parameters:**
- `icao24` (str): Aircraft ICAO24 address
- `begin_time` (datetime): Start time
- `end_time` (datetime): End time (max 30 days from begin_time)

**Returns:** List of FlightData objects

### Data Models

#### StateVector

Represents the state of an aircraft at a specific time.

**Properties:**
- `icao24` (str): ICAO24 address
- `callsign` (str): Aircraft callsign
- `origin_country` (str): Country of origin
- `time_position` (int): Timestamp of position
- `last_contact` (int): Last contact timestamp
- `longitude` (float): Longitude in decimal degrees
- `latitude` (float): Latitude in decimal degrees
- `baro_altitude` (float): Barometric altitude in meters
- `on_ground` (bool): Whether aircraft is on ground
- `velocity` (float): Ground speed in m/s
- `true_track` (float): True track angle in degrees
- `vertical_rate` (float): Vertical rate in m/s
- `sensors` (List[int]): Sensor IDs
- `geo_altitude` (float): Geometric altitude in meters
- `squawk` (str): Squawk code
- `spi` (bool): Special purpose indicator
- `position_source` (int): Position source indicator

#### OpenSkyStates

Container for multiple aircraft states.

**Properties:**
- `time` (int): Timestamp of data
- `states` (List[StateVector]): List of aircraft states

#### FlightData

Represents a flight with departure/arrival information.

**Properties:**
- `icao24` (str): Aircraft ICAO24 address
- `first_seen` (int): First seen timestamp
- `est_departure_airport` (str): Estimated departure airport
- `last_seen` (int): Last seen timestamp
- `est_arrival_airport` (str): Estimated arrival airport
- `callsign` (str): Flight callsign

#### BoundingBox

Defines a geographic area.

**Properties:**
- `lat_min` (float): Minimum latitude
- `lat_max` (float): Maximum latitude
- `lon_min` (float): Minimum longitude
- `lon_max` (float): Maximum longitude

### Utility Functions

#### OpenSkyUtils

Collection of utility functions for working with OpenSky data.

##### validate_icao24()

```python
@staticmethod
def validate_icao24(icao24: str) -> bool
```

Validate ICAO24 format (6 hexadecimal characters).

##### datetime_to_timestamp()

```python
@staticmethod
def datetime_to_timestamp(dt: datetime) -> int
```

Convert datetime to Unix timestamp.

##### calculate_distance()

```python
@staticmethod
def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float
```

Calculate distance between two coordinates in kilometers.

##### create_bounding_box()

```python
@staticmethod
def create_bounding_box(center_lat: float, center_lon: float, radius_km: float) -> BoundingBox
```

Create bounding box around a center point.

##### states_to_dataframe()

```python
@staticmethod
def states_to_dataframe(states: List[StateVector]) -> pd.DataFrame
```

Convert aircraft states to pandas DataFrame.

## Configuration

### OpenSkyConfig

Configuration management class.

**Properties:**
- `base_url` (str): API base URL
- `timeout` (int): Request timeout in seconds
- `max_retries` (int): Maximum retry attempts
- `rate_limit_delay` (float): Delay between requests
- `cache_duration` (int): Cache TTL in seconds
- `username` (str): API username
- `password` (str): API password

**Methods:**
- `load_credentials()`: Load credentials from file
- `is_authenticated()`: Check if credentials are available

## Error Handling

The integration provides comprehensive error handling for common scenarios:

### API Errors

- **401 Unauthorized**: Invalid credentials
- **403 Forbidden**: Access denied
- **429 Too Many Requests**: Rate limit exceeded
- **500+ Server Errors**: OpenSky server issues

### Network Errors

- **Connection Timeout**: Request timeout
- **Connection Error**: Network connectivity issues
- **DNS Resolution**: Domain name resolution failures

### Data Validation Errors

- **Invalid ICAO24**: Malformed aircraft identifiers
- **Invalid Coordinates**: Out-of-range latitude/longitude
- **Invalid Time Range**: Time range too large or invalid

### Example Error Handling

```python
try:
    states = await service.get_states()
except Exception as e:
    if "401" in str(e):
        print("Authentication failed - check credentials")
    elif "429" in str(e):
        print("Rate limit exceeded - wait before retrying")
    elif "timeout" in str(e).lower():
        print("Request timed out - check network connection")
    else:
        print(f"Unexpected error: {e}")
```

## Performance Optimization

### Rate Limiting

The service automatically enforces rate limits:
- **Unauthenticated**: 10 seconds between requests
- **Authenticated**: 5 seconds between requests (configurable)

### Caching

Intelligent caching reduces API calls:
- **TTL-based**: Configurable cache duration (default 10 seconds)
- **Request-specific**: Different cache keys for different requests
- **Memory-efficient**: Automatic cache cleanup

### Best Practices

1. **Use Authentication**: Authenticated requests have higher rate limits
2. **Cache Results**: Don't make identical requests within cache duration
3. **Batch Requests**: Use bounding boxes instead of multiple single-aircraft requests
4. **Filter Data**: Use geographic filters to reduce data volume
5. **Handle Errors**: Implement retry logic with exponential backoff

## Testing

### Running Tests

```bash
# Run all tests
python -m pytest tests/test_opensky_clean.py -v

# Run specific test class
python -m pytest tests/test_opensky_clean.py::TestOpenSkyService -v

# Run integration tests (requires credentials)
python -m pytest tests/test_opensky_clean.py::TestIntegrationScenarios -v
```

### Test Coverage

The test suite covers:
- Configuration management
- API service functionality
- Error handling scenarios
- Data model validation
- Utility functions
- Integration scenarios

## Examples

### Real-time Tracking

```python
async def track_aircraft():
    service = OpenSkyService()
    
    # Define monitoring area
    bbox = BoundingBox(lat_min=40.0, lat_max=41.0, lon_min=-75.0, lon_max=-73.0)
    
    while True:
        states = await service.get_states(bbox=bbox)
        print(f"Tracking {len(states.states)} aircraft")
        
        for aircraft in states.states[:5]:  # Show first 5
            print(f"{aircraft.callsign}: {aircraft.latitude:.4f}, {aircraft.longitude:.4f}")
        
        await asyncio.sleep(30)  # Update every 30 seconds
```

### Historical Analysis

```python
async def analyze_airport_traffic():
    service = OpenSkyService()
    
    # Analyze last 2 hours
    end_time = datetime.now()
    begin_time = end_time - timedelta(hours=2)
    
    flights = await service.get_flights(begin_time, end_time)
    
    # Count departures by airport
    departures = {}
    for flight in flights:
        if flight.est_departure_airport:
            departures[flight.est_departure_airport] = departures.get(flight.est_departure_airport, 0) + 1
    
    # Show top airports
    sorted_airports = sorted(departures.items(), key=lambda x: x[1], reverse=True)
    for airport, count in sorted_airports[:10]:
        print(f"{airport}: {count} departures")
```

### Data Export

```python
async def export_aircraft_data():
    service = OpenSkyService()
    
    states = await service.get_states()
    df = OpenSkyUtils.states_to_dataframe(states.states)
    
    # Export to CSV
    df.to_csv("aircraft_data.csv", index=False)
    
    # Basic analysis
    print(f"Total aircraft: {len(df)}")
    print(f"Average altitude: {df['baro_altitude'].mean():.0f} m")
    print(f"Countries: {df['origin_country'].nunique()}")
```

## Troubleshooting

### Common Issues

#### Authentication Errors

**Problem**: 401 Unauthorized responses
**Solution**: 
1. Verify credentials in `credentials.json`
2. Check username/password are correct
3. Ensure OpenSky account is active

#### Rate Limiting

**Problem**: 429 Too Many Requests
**Solution**:
1. Implement proper delays between requests
2. Use authentication for higher limits
3. Cache results to reduce API calls

#### No Data Returned

**Problem**: Empty results from API
**Solution**:
1. Check geographic bounds are reasonable
2. Verify ICAO24 addresses are valid
3. Try broader search parameters

#### Timeout Errors

**Problem**: Requests timing out
**Solution**:
1. Check network connectivity
2. Increase timeout value in config
3. Implement retry logic

### Debug Mode

Enable debug logging to troubleshoot issues:

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Service will now log detailed information
service = OpenSkyService()
```

### Support

For additional support:
1. Check OpenSky Network documentation
2. Review integration tests for examples
3. Check configuration settings
4. Verify API limits and quotas

## Changelog

### Version 1.0.0
- Initial release with full async support
- Comprehensive error handling
- Production-ready caching and rate limiting
- Complete test suite
- Full documentation

---

*This integration is designed for production use in Air Traffic Control systems with emphasis on reliability, performance, and data accuracy.*
states = service.get_current_states(icao24="a835af")
```

##### get_my_sensor_states()

```python
get_my_sensor_states(icao24=None, serials=None) -> OpenSkyStates
```

Retrieve states from authenticated user's sensors (requires authentication).

**Parameters:**
- `icao24` (str or List[str], optional): Specific aircraft
- `serials` (List[int], optional): Specific sensor serial numbers

#### Historical Data Methods

##### get_flights_in_timerange()

```python
get_flights_in_timerange(begin, end) -> List[FlightData]
```

Retrieve flights in time range (maximum 2 hours).

**Parameters:**
- `begin` (int): Start time (Unix timestamp)
- `end` (int): End time (Unix timestamp)

**Example:**
```python
import time
end_time = int(time.time())
start_time = end_time - 3600  # 1 hour ago
flights = service.get_flights_in_timerange(start_time, end_time)
```

##### get_aircraft_flights()

```python
get_aircraft_flights(icao24, begin, end) -> List[FlightData]
```

Retrieve flights for specific aircraft (maximum 30 days).

**Example:**
```python
# Get last week's flights for specific aircraft
end_time = int(time.time())
start_time = end_time - (7 * 24 * 3600)  # 7 days ago
flights = service.get_aircraft_flights("a835af", start_time, end_time)
```

##### get_airport_arrivals() / get_airport_departures()

```python
get_airport_arrivals(airport_icao, begin, end) -> List[FlightData]
get_airport_departures(airport_icao, begin, end) -> List[FlightData]
```

Retrieve airport traffic (maximum 7 days).

**Example:**
```python
# Get today's arrivals at JFK
end_time = int(time.time())
start_time = end_time - 86400  # 24 hours ago
arrivals = service.get_airport_arrivals("KJFK", start_time, end_time)
```

##### get_aircraft_track()

```python
get_aircraft_track(icao24, timestamp=0) -> FlightTrack
```

Retrieve aircraft trajectory (0 for live track).

**Example:**
```python
# Get live track
track = service.get_aircraft_track("a835af")

# Get historical track
track = service.get_aircraft_track("a835af", 1609459200)
```

### Data Models

#### StateVector

Represents an aircraft's state at a specific time.

**Key Properties:**
- `icao24`: Unique ICAO 24-bit address
- `callsign`: Aircraft callsign
- `latitude`, `longitude`: Position coordinates
- `baro_altitude`: Barometric altitude in meters
- `velocity`: Ground speed in m/s
- `true_track`: True track in degrees
- `on_ground`: Whether aircraft is on ground

**Methods:**
- `has_position`: Check if valid position data exists
- `distance_to(other)`: Calculate distance to another aircraft

#### BoundingBox

Geographic area for filtering aircraft.

```python
bbox = BoundingBox(
    min_latitude=40.0,
    max_latitude=41.0,
    min_longitude=-74.0,
    max_longitude=-73.0
)
```

#### FlightData

Flight information including departure and arrival details.

**Key Properties:**
- `icao24`: Aircraft identifier
- `callsign`: Flight callsign
- `est_departure_airport`: Departure airport ICAO
- `est_arrival_airport`: Arrival airport ICAO
- `first_seen`, `last_seen`: Flight timestamps

### Utility Functions

#### Geographic Functions

```python
from utils.opensky_utils import *

# Create bounding box around point
bbox = create_bounding_box(40.7128, -74.0060, 100)  # 100km radius around NYC

# Calculate distance between points
distance = haversine_distance(lat1, lon1, lat2, lon2)

# Filter aircraft by distance
nearby = filter_states_by_distance(states, center_lat, center_lon, max_km)
```

#### Data Conversion

```python
# Convert to pandas DataFrame
df = states_to_dataframe(state_list)
flights_df = flights_to_dataframe(flight_list)

# Calculate track statistics
stats = calculate_track_statistics(waypoints)
```

#### Validation

```python
# Validate ICAO codes
is_valid = validate_icao24("a835af")
normalized = normalize_icao24("A835AF")  # Returns "a835af"

is_valid_airport = validate_icao_airport("KJFK")
```

## Configuration

### Environment-based Configuration

```python
from config.opensky_config import OpenSkyConfig, Environment

# Development environment (longer timeouts, more retries)
config = OpenSkyConfig(environment=Environment.DEVELOPMENT)

# Production environment (optimized for performance)
config = OpenSkyConfig(environment=Environment.PRODUCTION)

# Testing environment (minimal timeouts, short cache)
config = OpenSkyConfig(environment=Environment.TESTING)
```

### Configuration Options

- **Timeouts**: Request timeout in seconds
- **Retries**: Maximum retry attempts
- **Rate Limiting**: Minimum time between requests
- **Caching**: Cache TTL and maximum size
- **Logging**: Configurable logging levels

## Error Handling

### Exception Types

- `OpenSkyAPIException`: API-related errors
- `ValueError`: Invalid parameters or data
- `FileNotFoundError`: Missing credentials file

### Error Scenarios

```python
try:
    states = service.get_current_states()
except OpenSkyAPIException as e:
    print(f"API Error: {e}")
    print(f"Status Code: {e.status_code}")
    print(f"Response: {e.response_data}")
```

### Common Error Codes

- **401 Unauthorized**: Invalid credentials
- **429 Too Many Requests**: Rate limit exceeded
- **400 Bad Request**: Invalid parameters
- **500 Internal Server Error**: OpenSky server issues

## Rate Limiting

### Limits

- **Unauthenticated**: 10 seconds between requests
- **Authenticated**: Faster requests (varies by endpoint)
- **Historical data**: Additional limits apply

### Best Practices

1. Use authentication for better rate limits
2. Cache responses when possible
3. Use bounding boxes to reduce data volume
4. Batch requests when feasible

### Rate Limit Handling

The service automatically handles rate limiting:

```python
# Automatic rate limiting - no need to worry about timing
states1 = service.get_current_states()
states2 = service.get_current_states()  # Will wait if needed
```

## Caching

### Cache Configuration

```python
# Default cache settings
cache_ttl = 300  # 5 minutes
max_cache_size = 128  # entries

# Check cache status
info = service.get_cache_info()
print(f"Cache size: {info['cache_size']}/{info['max_size']}")

# Clear cache manually
service.clear_cache()
```

### Cache Keys

Cache keys are automatically generated based on endpoint and parameters. Identical requests within the TTL period will return cached results.

## Performance Optimization

### Best Practices

1. **Use appropriate bounding boxes**: Smaller areas = faster responses
2. **Cache responses**: Avoid redundant API calls
3. **Filter data locally**: Use utility functions for additional filtering
4. **Batch operations**: Process multiple aircraft together

### Performance Monitoring

```python
# Response time is included in APIResponse
response = service._make_request("states/all")
print(f"Response time: {response.response_time:.3f}s")
```

## Testing

### Unit Tests

```python
# Run all tests
python -m tests.test_opensky_service

# Run specific test
python -m unittest tests.test_opensky_service.TestOpenSkyService.test_get_current_states_success
```

### Mock Testing

```python
from unittest.mock import patch, MagicMock

@patch('services.opensky_service.requests.Session.get')
def test_my_function(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {"time": 1609459200, "states": []}
    mock_response.status_code = 200
    mock_get.return_value = mock_response
    
    # Your test code here
```

## Examples and Use Cases

### Real-time Air Traffic Monitoring

```python
# Monitor aircraft around major airport
airport_bbox = create_bounding_box(40.6413, -73.7781, 50)  # 50km around JFK
states = service.get_current_states(bbox=airport_bbox)

for aircraft in states.states:
    if aircraft.has_position and aircraft.baro_altitude:
        print(f"{aircraft.callsign}: {aircraft.baro_altitude}m altitude")
```

### Flight Tracking Dashboard

```python
# Track specific flights
tracked_aircraft = ["a835af", "a0f842", "a1c2fd"]
states = service.get_current_states(icao24=tracked_aircraft)

# Convert to DataFrame for dashboard
df = states_to_dataframe(states.states)
```

### Airport Traffic Analysis

```python
# Analyze airport traffic patterns
end_time = int(time.time())
start_time = end_time - 86400  # 24 hours

arrivals = service.get_airport_arrivals("KJFK", start_time, end_time)
departures = service.get_airport_departures("KJFK", start_time, end_time)

print(f"JFK Traffic: {len(arrivals)} arrivals, {len(departures)} departures")
```

### Historical Flight Analysis

```python
# Analyze aircraft utilization
aircraft = "a835af"
end_time = int(time.time())
start_time = end_time - (7 * 24 * 3600)  # 7 days

flights = service.get_aircraft_flights(aircraft, start_time, end_time)
total_flight_time = sum(f.flight_duration_seconds for f in flights)
print(f"Total flight time: {total_flight_time / 3600:.1f} hours")
```

## Troubleshooting

### Common Issues

#### Authentication Problems

```
Error: 401 Unauthorized
```

**Solutions:**
1. Check credentials.json format
2. Verify username/password
3. Ensure file path is correct

#### Rate Limiting

```
Error: 429 Too Many Requests
```

**Solutions:**
1. Increase delays between requests
2. Use authentication for better limits
3. Implement exponential backoff

#### No Data Returned

**Possible Causes:**
1. Aircraft not in specified area
2. Aircraft not currently flying
3. API rate limits

**Solutions:**
1. Expand search area
2. Check different time periods
3. Verify API status

#### Large Response Times

**Solutions:**
1. Use smaller bounding boxes
2. Enable caching
3. Filter results locally

### Debugging

#### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### Check Configuration

```python
config = get_config()
validation = config.validate_config()
print(validation)
```

#### Monitor API Calls

```python
# Check cache efficiency
info = service.get_cache_info()
print(f"Cache hit ratio: {info}")

# Monitor response times
response = service._make_request("states/all")
print(f"Response time: {response.response_time}s")
```

## API Limits and Constraints

### OpenSky Network Limits

1. **Unauthenticated Users**: 10 seconds between requests
2. **Authenticated Users**: No rate limit for own sensor data
3. **Historical Data**: 
   - Flight intervals: Maximum 2 hours
   - Aircraft history: Maximum 30 days
   - Airport queries: Maximum 7 days

### Data Constraints

1. **ICAO24 Format**: Must be 6-character lowercase hexadecimal
2. **Airport Codes**: Must be 4-character ICAO format
3. **Coordinates**: WGS-84 decimal degrees
4. **Timestamps**: Unix time (seconds since epoch)

### Best Practices Summary

1. **Authentication**: Use credentials for better performance
2. **Caching**: Enable caching to reduce API calls
3. **Error Handling**: Always handle API exceptions
4. **Rate Limiting**: Respect API limits
5. **Data Validation**: Validate inputs before API calls
6. **Monitoring**: Track performance and errors
7. **Testing**: Use mocks for unit tests

---

This documentation provides a comprehensive guide to using the OpenSky Network API integration. For additional examples and advanced usage, see the `examples/` directory in the project.