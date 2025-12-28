# 🚀 **REAL-TIME APIs INTEGRATION GUIDE**

## **Complete Setup Instructions for FREE APIs**

---

## 🌐 **API 1: OpenSky Network (FREE)**

### **What You Get:**
- ✅ Real-time flight positions worldwide
- ✅ Aircraft data (callsign, altitude, speed, heading)
- ✅ Flight tracks and history
- ✅ Airport arrivals/departures

### **How to Get FREE Access:**

1. **Go to:** https://opensky-network.org/
2. **Click:** "Register" (top right corner)
3. **Fill out:** Simple registration form
4. **Get:** Username and Password (FREE!)

### **Rate Limits (FREE):**
- ✅ **10 requests per minute** (6 seconds between calls)
- ✅ **Unlimited data** (no daily limits)
- ✅ **No credit card required**

### **Integration Code:**
```python
from core.api_services.opensky_integration import OpenSkyIntegration

# Initialize with your credentials
opensky = OpenSkyIntegration(
    username="YOUR_USERNAME",  # From registration
    password="YOUR_PASSWORD"   # From registration
)

# Get flights in New York area
flights = opensky.get_flights_by_area(
    min_lat=40.0, max_lat=41.0,
    min_lon=-75.0, max_lon=-73.0
)

print(f"Found {len(flights)} flights!")
```

---

## 🌤️ **API 2: OpenWeatherMap (FREE)**

### **What You Get:**
- ✅ Real-time weather conditions
- ✅ 5-day weather forecasts
- ✅ Weather alerts and warnings
- ✅ Aviation weather data
- ✅ Air pollution data

### **How to Get FREE Access:**

1. **Go to:** https://openweathermap.org/api
2. **Click:** "Sign Up" (top right)
3. **Fill out:** Registration form
4. **Get:** API Key (FREE!)

### **Rate Limits (FREE):**
- ✅ **1000 calls per day**
- ✅ **60 calls per minute**
- ✅ **No credit card required**

### **Integration Code:**
```python
from core.api_services.openweathermap_integration import OpenWeatherMapIntegration

# Initialize with your API key
weather = OpenWeatherMapIntegration(
    api_key="YOUR_API_KEY"  # From registration
)

# Get weather for New York
weather_data = weather.get_current_weather(40.7128, -74.0060)

print(f"Weather: {weather_data.temperature}°C")
print(f"Conditions: {weather_data.weather_description}")
```

---

## 🛬 **API 3: FAA Airport Status (FREE)**

### **What You Get:**
- ✅ Airport delay information
- ✅ Runway status
- ✅ Weather conditions at airports
- ✅ NOTAMs (Notices to Airmen)
- ✅ Ground traffic status

### **How to Get FREE Access:**

1. **Go to:** https://www.faa.gov/data_research/
2. **Navigate:** Airport Status APIs
3. **Access:** Public APIs (no registration needed)
4. **Use:** Direct API calls (FREE!)

### **Rate Limits (FREE):**
- ✅ **No official limits** (be respectful)
- ✅ **1 second between calls** recommended
- ✅ **No API key required**

### **Integration Code:**
```python
from core.api_services.faa_integration import FAAIntegration

# Initialize (no credentials needed)
faa = FAAIntegration()

# Get JFK airport status
status = faa.get_airport_status("JFK")

print(f"JFK Status: {status.delay_status}")
print(f"Delay: {status.delay_minutes} minutes")
```

---

## 🔧 **Complete Setup Instructions**

### **Step 1: Get Your API Keys**

1. **OpenSky Network:**
   - Register at: https://opensky-network.org/
   - Get: Username + Password

2. **OpenWeatherMap:**
   - Register at: https://openweathermap.org/api
   - Get: API Key

3. **FAA:**
   - No registration needed
   - Direct access to public APIs

### **Step 2: Configure Your System**

Create a configuration file `config/api_keys.py`:

```python
# API Configuration
API_KEYS = {
    "opensky": {
        "username": "YOUR_OPENSKY_USERNAME",
        "password": "YOUR_OPENSKY_PASSWORD"
    },
    "openweathermap": {
        "api_key": "YOUR_OPENWEATHERMAP_API_KEY"
    },
    "faa": {
        "api_key": None  # No key needed
    }
}
```

### **Step 3: Test Your APIs**

Run the test script:

```bash
python core/api_services/unified_api_manager.py
```

### **Step 4: Use in Your Application**

```python
from core.api_services.unified_api_manager import UnifiedAPIManager

# Initialize manager
manager = UnifiedAPIManager()

# Configure APIs
manager.configure_api("opensky", APIConfig(
    service_name="OpenSky Network",
    enabled=True,
    username="YOUR_USERNAME",
    password="YOUR_PASSWORD"
))

manager.configure_api("openweathermap", APIConfig(
    service_name="OpenWeatherMap",
    enabled=True,
    api_key="YOUR_API_KEY"
))

# Initialize and start
manager.initialize_apis()
manager.start_background_updates()

# Get data
flights = manager.get_flights_in_area(40.0, 41.0, -75.0, -73.0)
weather = manager.get_weather_at_location(40.7128, -74.0060)
airport = manager.get_airport_status("JFK")
```

---

## 📊 **Data You'll Get**

### **Flight Data:**
```json
{
  "icao24": "ABC123",
  "callsign": "FL123",
  "latitude": 40.7128,
  "longitude": -74.0060,
  "altitude": 35000,
  "velocity": 500,
  "heading": 90,
  "vertical_rate": 0
}
```

### **Weather Data:**
```json
{
  "location": "New York",
  "temperature": 22.5,
  "humidity": 65,
  "wind_speed": 15,
  "weather_description": "Partly cloudy",
  "visibility": 10
}
```

### **Airport Status:**
```json
{
  "airport_code": "JFK",
  "delay_status": "Minor Delays",
  "delay_minutes": 15,
  "delay_reason": "Weather",
  "weather_conditions": "Rain"
}
```

---

## 🚀 **Quick Start Commands**

### **Test OpenSky:**
```bash
python core/api_services/opensky_integration.py
```

### **Test OpenWeatherMap:**
```bash
python core/api_services/openweathermap_integration.py
```

### **Test FAA:**
```bash
python core/api_services/faa_integration.py
```

### **Test All APIs:**
```bash
python core/api_services/unified_api_manager.py
```

---

## ⚠️ **Important Notes**

### **Rate Limiting:**
- **OpenSky:** 6 seconds between calls
- **OpenWeatherMap:** 1 second between calls
- **FAA:** 1 second between calls

### **Error Handling:**
- All APIs include automatic retry logic
- Fallback to mock data if APIs fail
- Comprehensive error logging

### **Data Quality:**
- Real-time data updates every 60 seconds
- Automatic data validation
- Performance metrics tracking

---

## 🎯 **Next Steps**

1. **Get your API keys** (5 minutes)
2. **Configure the system** (2 minutes)
3. **Test the integration** (1 minute)
4. **Start collecting real data!** 🚀

---

## 📞 **Need Help?**

- **OpenSky Issues:** Check https://opensky-network.org/forum/
- **OpenWeatherMap Issues:** Check https://openweathermap.org/help
- **FAA Issues:** Check https://www.faa.gov/data_research/

---

## 🏆 **What You've Built**

✅ **Real-time flight tracking**  
✅ **Live weather monitoring**  
✅ **Airport status tracking**  
✅ **Unified data management**  
✅ **Automatic background updates**  
✅ **Performance monitoring**  
✅ **Error handling & retry logic**  

**Your ATC AI system now has LIVE DATA!** 🎉


