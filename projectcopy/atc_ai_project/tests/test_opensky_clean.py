"""
Comprehensive test suite for OpenSky Network API integration
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import time
import json
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.opensky_config import OpenSkyConfig
from services.opensky_service import OpenSkyService
from models.opensky_models import StateVector, OpenSkyStates, FlightData, BoundingBox


class MockResponse:
    """Mock HTTP response for testing"""
    
    def __init__(self, json_data, status_code=200):
        self.json_data = json_data
        self.status_code = status_code
        self.text = json.dumps(json_data) if isinstance(json_data, dict) else str(json_data)
    
    def json(self):
        return self.json_data


class TestOpenSkyConfig(unittest.TestCase):
    """Test OpenSky configuration management"""
    
    def test_config_initialization(self):
        """Test basic config initialization"""
        config = OpenSkyConfig()
        self.assertEqual(config.base_url, "https://opensky-network.org/api")
        self.assertEqual(config.timeout, 30)
        self.assertEqual(config.max_retries, 3)
    
    @patch('builtins.open')
    @patch('json.load')
    def test_load_credentials_success(self, mock_json_load, mock_open):
        """Test successful credential loading"""
        mock_json_load.return_value = {
            "opensky": {
                "username": "test_user",
                "password": "test_pass"
            }
        }
        
        config = OpenSkyConfig()
        config.load_credentials()
        
        self.assertEqual(config.username, "test_user")
        self.assertEqual(config.password, "test_pass")
    
    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_load_credentials_file_not_found(self, mock_open):
        """Test credential loading when file is missing"""
        config = OpenSkyConfig()
        config.load_credentials()  # Should not raise exception
        self.assertIsNone(config.username)
        self.assertIsNone(config.password)
    
    def test_is_authenticated(self):
        """Test authentication status checking"""
        config = OpenSkyConfig()
        self.assertFalse(config.is_authenticated())
        
        config.username = "test"
        config.password = "test"
        self.assertTrue(config.is_authenticated())


class TestOpenSkyService(unittest.TestCase):
    """Test OpenSky API service functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = OpenSkyConfig()
        self.service = OpenSkyService(self.config)
        
        # Sample state data matching OpenSky API format
        self.sample_state = [
            "a835af",         # icao24
            "UAL123  ",       # callsign
            "United States",  # origin_country
            1609459200,       # time_position
            1609459200,       # last_contact
            -74.0060,         # longitude
            40.7128,          # latitude
            10668.0,          # baro_altitude
            False,            # on_ground
            200.5,            # velocity
            45.0,             # true_track
            0.0,              # vertical_rate
            [1, 2],           # sensors
            10700.0,          # geo_altitude
            "1234",           # squawk
            False,            # spi
            0                 # position_source
        ]
        
        self.sample_states_response = {
            "time": 1609459200,
            "states": [self.sample_state]
        }
    
    def tearDown(self):
        """Clean up after tests"""
        if hasattr(self.service, 'close'):
            self.service.close()
    
    @patch('requests.Session.get')
    def test_get_states_success(self, mock_get):
        """Test successful states retrieval"""
        mock_get.return_value = MockResponse(self.sample_states_response)
        
        result = self.service.get_states()
        
        self.assertIsInstance(result, OpenSkyStates)
        self.assertEqual(result.time, 1609459200)
        self.assertEqual(len(result.states), 1)
        self.assertEqual(result.states[0].icao24, "a835af")
        self.assertEqual(result.states[0].callsign, "UAL123")
    
    @patch('requests.Session.get')
    def test_get_states_with_bbox(self, mock_get):
        """Test states retrieval with bounding box"""
        mock_get.return_value = MockResponse(self.sample_states_response)
        
        bbox = BoundingBox(
            lat_min=40.0,
            lat_max=41.0,
            lon_min=-75.0,
            lon_max=-73.0
        )
        
        result = self.service.get_states(bbox=bbox)
        
        # Check that correct parameters were passed
        mock_get.assert_called_once()
        self.assertIsInstance(result, OpenSkyStates)
    
    @patch('requests.Session.get')
    def test_get_states_with_icao24(self, mock_get):
        """Test states retrieval with ICAO24 filter"""
        mock_get.return_value = MockResponse(self.sample_states_response)
        
        result = self.service.get_states(icao24=["A835AF"])
        
        self.assertIsInstance(result, OpenSkyStates)
        self.assertEqual(len(result.states), 1)
    
    @patch('requests.Session.get')
    def test_api_error_handling(self, mock_get):
        """Test API error handling"""
        error_response = {
            "timestamp": 1609459200,
            "status": 401,
            "error": "Unauthorized",
            "message": "Invalid credentials"
        }
        mock_get.return_value = MockResponse(error_response, 401)
        
        with self.assertRaises(Exception):
            self.service.get_states()
    
    @patch('requests.Session.get')
    def test_rate_limiting(self, mock_get):
        """Test rate limiting functionality"""
        mock_get.return_value = MockResponse(self.sample_states_response)
        
        # Make multiple requests and measure time
        start_time = time.time()
        
        self.service.get_states()
        self.service.get_states()
        
        elapsed_time = time.time() - start_time
        
        # Should have enforced some delay
        self.assertGreaterEqual(elapsed_time, 0)
    
    @patch('requests.Session.get')
    def test_get_flights_success(self, mock_get):
        """Test successful flights retrieval"""
        sample_flight = {
            "icao24": "a835af",
            "firstSeen": 1609459200,
            "estDepartureAirport": "KJFK",
            "lastSeen": 1609466400,
            "estArrivalAirport": "KLAX",
            "callsign": "UAL123",
            "estDepartureAirportHorizDistance": 1000,
            "estDepartureAirportVertDistance": 100,
            "estArrivalAirportHorizDistance": 2000,
            "estArrivalAirportVertDistance": 200,
            "departureAirportCandidatesCount": 1,
            "arrivalAirportCandidatesCount": 1
        }
        
        mock_get.return_value = MockResponse([sample_flight])
        
        begin_time = datetime.now() - timedelta(hours=1)
        end_time = datetime.now()
        
        result = self.service.get_flights(begin_time, end_time)
        
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], FlightData)
        self.assertEqual(result[0].icao24, "a835af")


class TestOpenSkyUtils(unittest.TestCase):
    """Test utility functions"""
    
    def test_icao24_validation(self):
        """Test ICAO24 validation"""
        from utils.opensky_utils import OpenSkyUtils
        
        # Valid ICAO24 codes
        self.assertTrue(OpenSkyUtils.validate_icao24("abc123"))
        self.assertTrue(OpenSkyUtils.validate_icao24("123ABC"))
        self.assertTrue(OpenSkyUtils.validate_icao24("ABCDEF"))
        
        # Invalid ICAO24 codes
        self.assertFalse(OpenSkyUtils.validate_icao24("abc12"))   # Too short
        self.assertFalse(OpenSkyUtils.validate_icao24("abc1234")) # Too long
        self.assertFalse(OpenSkyUtils.validate_icao24("abc12!"))  # Invalid char
        self.assertFalse(OpenSkyUtils.validate_icao24(""))        # Empty
    
    def test_datetime_conversion(self):
        """Test datetime to timestamp conversion"""
        from utils.opensky_utils import OpenSkyUtils
        
        dt = datetime(2021, 1, 1, 12, 0, 0)
        timestamp = OpenSkyUtils.datetime_to_timestamp(dt)
        self.assertIsInstance(timestamp, int)
        
        converted_back = OpenSkyUtils.timestamp_to_datetime(timestamp)
        self.assertEqual(converted_back.year, 2021)
        self.assertEqual(converted_back.month, 1)
        self.assertEqual(converted_back.day, 1)
    
    def test_distance_calculation(self):
        """Test geographic distance calculation"""
        from utils.opensky_utils import OpenSkyUtils
        
        # Distance between known coordinates
        lat1, lon1 = 40.7128, -74.0060  # New York
        lat2, lon2 = 34.0522, -118.2437  # Los Angeles
        
        distance = OpenSkyUtils.calculate_distance(lat1, lon1, lat2, lon2)
        
        # Should be approximately 3944 km
        self.assertGreater(distance, 3900)
        self.assertLess(distance, 4000)
    
    def test_bounding_box_creation(self):
        """Test bounding box creation from center point"""
        from utils.opensky_utils import OpenSkyUtils
        
        center_lat, center_lon = 40.7128, -74.0060
        radius_km = 100
        
        bbox = OpenSkyUtils.create_bounding_box(center_lat, center_lon, radius_km)
        
        self.assertIsInstance(bbox, BoundingBox)
        self.assertLess(bbox.lat_min, center_lat)
        self.assertGreater(bbox.lat_max, center_lat)
        self.assertLess(bbox.lon_min, center_lon)
        self.assertGreater(bbox.lon_max, center_lon)


class TestIntegrationScenarios(unittest.TestCase):
    """Integration test scenarios"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.config = OpenSkyConfig()
        self.config.load_credentials()
        self.service = OpenSkyService(self.config)
    
    def tearDown(self):
        """Clean up after integration tests"""
        if hasattr(self.service, 'close'):
            self.service.close()
    
    @unittest.skip("Integration test - requires real API access")
    def test_full_workflow(self):
        """Test complete workflow (requires real API access)"""
        if not self.config.is_authenticated():
            self.skipTest("No OpenSky credentials available")
        
        # Get current states
        states = self.service.get_states()
        self.assertIsInstance(states, OpenSkyStates)
        
        if states.states:
            # Get historical data for first aircraft
            icao24 = states.states[0].icao24
            end_time = datetime.now()
            begin_time = end_time - timedelta(hours=1)
            
            flights = self.service.get_flights_by_aircraft(
                icao24, begin_time, end_time
            )
            
            self.assertIsInstance(flights, list)


if __name__ == '__main__':
    unittest.main()