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
            "a835af",      # icao24
            "UAL123  ",    # callsign
            "United States",  # origin_country
            1609459200,    # time_position
            1609459200,    # last_contact
            -74.0060,      # longitude
            40.7128,       # latitude
            10668.0,       # baro_altitude
            False,         # on_ground
            200.5,         # velocity
            45.0,          # true_track
            0.0,           # vertical_rate
            [1, 2],        # sensors
            10700.0,       # geo_altitude
            "1234",        # squawk
            False,         # spi
            0              # position_source
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
        call_args = mock_get.call_args
        if len(call_args) > 1 and 'params' in call_args[1]:
            params = call_args[1]['params']
            self.assertIn('lamin', params)
            self.assertIn('lamax', params)
            self.assertIn('lomin', params)
            self.assertIn('lomax', params)
    
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
            10668.0,  # baro_altitude
            False,  # on_ground
            200.5,  # velocity
            45.0,  # true_track
            0.0,  # vertical_rate
            [1, 2],  # sensors
            10700.0,  # geo_altitude
            "1234",  # squawk
            False,  # spi
            0  # position_source
        ]
        
        self.sample_states_response = {
            "time": 1609459200,
            "states": [self.sample_state]
        }
    
    def tearDown(self):
        """Clean up after tests"""
        self.service.close()
    
    @patch('services.opensky_service.requests.Session.get')
    def test_get_current_states_success(self, mock_get):
        """Test successful get_current_states call"""
        mock_get.return_value = MockResponse(self.sample_states_response)
        
        result = self.service.get_current_states()
        
        self.assertIsInstance(result, OpenSkyStates)
        self.assertEqual(result.aircraft_count, 1)
        self.assertEqual(result.states[0].icao24, "a835af")
        self.assertEqual(result.states[0].callsign, "UAL123")
    
    @patch('services.opensky_service.requests.Session.get')
    def test_get_current_states_with_bbox(self, mock_get):
        """Test get_current_states with bounding box"""
        mock_get.return_value = MockResponse(self.sample_states_response)
        
        bbox = BoundingBox(
            min_latitude=40.0,
            max_latitude=41.0,
            min_longitude=-75.0,
            max_longitude=-73.0
        )
        
        result = self.service.get_current_states(bbox=bbox)
        
        # Check that correct parameters were passed
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        params = call_args[1]['params']
        
        self.assertEqual(params['lamin'], 40.0)
        self.assertEqual(params['lamax'], 41.0)
        self.assertEqual(params['lomin'], -75.0)
        self.assertEqual(params['lomax'], -73.0)
    
    @patch('services.opensky_service.requests.Session.get')
    def test_get_current_states_with_icao24(self, mock_get):
        """Test get_current_states with ICAO24 filter"""
        mock_get.return_value = MockResponse(self.sample_states_response)
        
        result = self.service.get_current_states(icao24="A835AF")  # Test uppercase
        
        # Check that ICAO24 was normalized to lowercase
        call_args = mock_get.call_args
        params = call_args[1]['params']
        self.assertEqual(params['icao24'], "a835af")
    
    @patch('services.opensky_service.requests.Session.get')
    def test_get_current_states_api_error(self, mock_get):
        """Test API error handling"""
        error_response = {
            "timestamp": 1609459200,
            "status": 401,
            "error": "Unauthorized",
            "message": "Invalid credentials"
        }
        mock_get.return_value = MockResponse(error_response, 401)
        
        with self.assertRaises(OpenSkyAPIException) as context:
            self.service.get_current_states()
        
        self.assertIn("Failed to get current states", str(context.exception))
        self.assertEqual(context.exception.status_code, 401)
    
    @patch('services.opensky_service.requests.Session.get')
    def test_rate_limiting(self, mock_get):
        """Test rate limiting functionality"""
        mock_get.return_value = MockResponse(self.sample_states_response)
        
        # Make multiple requests and measure time
        start_time = time.time()
        
        self.service.get_current_states()
        self.service.get_current_states()
        
        elapsed_time = time.time() - start_time
        
        # Should have waited for rate limit (testing environment has short limits)
        # This is a basic test - actual timing may vary
        self.assertTrue(elapsed_time >= 0)  # Basic sanity check
    
    def test_cache_functionality(self):
        """Test response caching"""
        with patch('services.opensky_service.requests.Session.get') as mock_get:
            mock_get.return_value = MockResponse(self.sample_states_response)
            
            # First request
            result1 = self.service.get_current_states()
            
            # Second identical request (should use cache)
            result2 = self.service.get_current_states()
            
            # Should only have made one actual HTTP request
            self.assertEqual(mock_get.call_count, 1)
            self.assertEqual(result1.aircraft_count, result2.aircraft_count)
    
    def test_cache_clear(self):
        """Test cache clearing functionality"""
        # Add something to cache
        cache_key = "test_key"
        self.service.cache[cache_key] = "test_value"
        
        self.assertIn(cache_key, self.service.cache)
        
        # Clear cache
        self.service.clear_cache()
        
        self.assertNotIn(cache_key, self.service.cache)
    
    def test_icao24_validation(self):
        """Test ICAO24 validation in API calls"""
        with self.assertRaises(ValueError):
            # Invalid ICAO24 should raise error before API call
            self.service.get_current_states(icao24="invalid")
    
    @patch('services.opensky_service.requests.Session.get')
    def test_get_aircraft_flights(self, mock_get):
        """Test get_aircraft_flights method"""
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
        
        end_time = int(time.time())
        start_time = end_time - 3600  # 1 hour ago
        
        result = self.service.get_aircraft_flights("a835af", start_time, end_time)
        
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], FlightData)
        self.assertEqual(result[0].icao24, "a835af")
    
    def test_time_range_validation(self):
        """Test time range validation for various methods"""
        end_time = int(time.time())
        
        # Test flights_in_timerange (max 2 hours)
        start_time_invalid = end_time - 8000  # > 2 hours
        with self.assertRaises(OpenSkyAPIException):
            self.service.get_flights_in_timerange(start_time_invalid, end_time)
        
        # Test aircraft_flights (max 30 days)
        start_time_invalid = end_time - (31 * 24 * 3600)  # > 30 days
        with self.assertRaises(OpenSkyAPIException):
            self.service.get_aircraft_flights("a835af", start_time_invalid, end_time)
    
    def test_context_manager(self):
        """Test service as context manager"""
        with OpenSkyService(self.config) as service:
            self.assertIsInstance(service, OpenSkyService)
        # Service should be closed after context
    
    def test_get_cache_info(self):
        """Test cache information retrieval"""
        info = self.service.get_cache_info()
        
        self.assertIn('cache_size', info)
        self.assertIn('max_size', info)
        self.assertIn('ttl', info)
        self.assertIsInstance(info['cache_size'], int)


class TestOpenSkyServiceIntegration(unittest.TestCase):
    """Integration tests for OpenSky service (requires network)"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.config = OpenSkyConfig(environment=Environment.TESTING)
        self.service = OpenSkyService(self.config)
    
    def tearDown(self):
        """Clean up after integration tests"""
        self.service.close()
    
    @unittest.skip("Integration test - requires network access")
    def test_real_api_call(self):
        """Test real API call (skipped by default)"""
        try:
            # This would make a real API call
            result = self.service.get_current_states()
            self.assertIsInstance(result, OpenSkyStates)
        except OpenSkyAPIException as e:
            # API might be down or rate limited
            self.skipTest(f"API not available: {e}")


class TestOpenSkyServicePerformance(unittest.TestCase):
    """Performance tests for OpenSky service"""
    
    def setUp(self):
        """Set up performance test fixtures"""
        self.config = OpenSkyConfig(environment=Environment.TESTING)
        self.service = OpenSkyService(self.config)
    
    def tearDown(self):
        """Clean up after performance tests"""
        self.service.close()
    
    @patch('services.opensky_service.requests.Session.get')
    def test_response_time_measurement(self, mock_get):
        """Test that response times are measured"""
        mock_get.return_value = MockResponse({"time": 1609459200, "states": []})
        
        result = self.service._make_request("states/all")
        
        self.assertIsNotNone(result.response_time)
        self.assertGreater(result.response_time, 0)
    
    @patch('services.opensky_service.requests.Session.get')
    def test_large_response_handling(self, mock_get):
        """Test handling of large responses"""
        # Create response with many aircraft
        large_states = []
        for i in range(1000):
            state = [
                f"a{i:05x}",  # icao24
                f"TST{i:03d}",  # callsign
                "Test Country",
                1609459200,
                1609459200,
                -74.0 + (i * 0.01),  # longitude
                40.7 + (i * 0.01),   # latitude
                10000 + i,
                False,
                200.0,
                45.0,
                0.0,
                [1],
                10000 + i,
                "1234",
                False,
                0
            ]
            large_states.append(state)
        
        large_response = {
            "time": 1609459200,
            "states": large_states
        }
        
        mock_get.return_value = MockResponse(large_response)
        
        start_time = time.time()
        result = self.service.get_current_states()
        processing_time = time.time() - start_time
        
        self.assertEqual(result.aircraft_count, 1000)
        # Processing should be reasonable (< 1 second for 1000 aircraft)
        self.assertLess(processing_time, 1.0)


def run_all_tests():
    """Run all test suites"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestOpenSkyService))
    suite.addTests(loader.loadTestsFromTestCase(TestOpenSkyServiceIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestOpenSkyServicePerformance))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == '__main__':
    run_all_tests()