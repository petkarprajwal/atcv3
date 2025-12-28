# ATC AI System - User Manual

## Getting Started

### Installation

1. **Download the project** to your computer
2. **Run the setup script**:
   - Windows: Double-click `setup.bat`
   - Mac/Linux: Run `bash setup.sh` in terminal

3. **Configure API credentials** (optional for demo):
   - Edit the `.env` file
   - Add your OpenSky Network and OpenWeatherMap API keys

4. **Start the application**:
   ```bash
   streamlit run dashboard/main.py
   ```

5. **Open your browser** to `http://localhost:8501`

### First Time Setup

#### API Credentials (Optional)

The system works in demo mode without API credentials, but for live data you'll need:

**OpenSky Network Account**:
1. Visit [opensky-network.org](https://opensky-network.org)
2. Create a free account
3. Note your username and password

**OpenWeatherMap API Key**:
1. Visit [openweathermap.org](https://openweathermap.org/api)
2. Sign up for a free account
3. Generate an API key

**Configure .env file**:
```
OPENSKY_USERNAME=your_username
OPENSKY_PASSWORD=your_password
OPENWEATHER_API_KEY=your_api_key
```

## Using the Dashboard

### Main Dashboard

The main dashboard provides an overview of the entire air traffic control system.

#### Key Metrics
- **Active Aircraft**: Number of currently tracked flights
- **Active Conflicts**: Number of potential collision scenarios
- **Scheduled Flights**: Flights scheduled on runways
- **Runway Utilization**: Percentage of runway capacity in use

#### Conflict Alerts
- Color-coded alerts based on severity:
  - 🔴 **CRITICAL**: Immediate attention required
  - 🟡 **HIGH/MEDIUM**: Monitor closely
  - 🟢 **LOW**: Routine monitoring

#### Flight Data Table
Real-time information about all tracked aircraft including:
- Callsign and country of origin
- Current altitude and speed
- Heading and position coordinates

#### Controls
- **Airport Selection**: Choose which airport region to monitor
- **Auto Refresh**: Automatically update data every 30 seconds
- **Manual Refresh**: Update data on demand

### Collision Avoidance Module

This module focuses on detecting and preventing mid-air conflicts.

#### Model Training
- Click **"Train Model"** to train the AI with synthetic data
- Training typically takes 30-60 seconds
- Model status shows if training is complete

#### Conflict Detection
- Real-time analysis of aircraft pairs
- ML-powered predictions with confidence scores
- Detailed conflict information including:
  - Time to potential conflict
  - Minimum separation distance
  - Severity classification

#### Features
- **Physics-based trajectory prediction**
- **Machine learning conflict probability**
- **Automated route suggestions** (planned feature)

### Runway Management Module

Optimize runway usage and minimize delays.

#### System Overview
- View all runways and their current status
- Monitor capacity utilization in real-time
- Track scheduled flights and delays

#### Runway Status
Each runway shows:
- **Capacity Utilization**: Percentage of maximum capacity
- **Next Hour Flights**: Flights scheduled in the next 60 minutes
- **Total Scheduled**: All scheduled flights
- **Upcoming Flights**: Next few flights with times

#### Scheduling New Flights
1. Enter flight details:
   - **Callsign**: Flight identifier
   - **Type**: Arrival or Departure
   - **Priority**: Normal, High, Urgent, or Emergency
   - **Fuel Level**: Current fuel percentage

2. Select preferred scheduling time

3. Click **"Schedule Flight"** to add to system

#### Priority System
- **EMERGENCY**: Immediate priority, may bump other flights
- **URGENT**: High priority, minimal delays
- **HIGH**: Elevated priority
- **NORMAL**: Standard scheduling

### Weather Integration Module

Monitor weather conditions and their impact on flight operations.

#### Weather Monitoring
1. Select an airport from the dropdown
2. Click **"Get Weather Data"** to fetch current conditions
3. View detailed weather information:
   - Temperature, humidity, pressure
   - Wind speed and direction
   - Visibility conditions

#### Weather Hazards
Automatic detection of potentially dangerous conditions:
- **Strong Winds**: >55 km/h
- **Low Visibility**: <5 km
- **Severe Weather**: Thunderstorms, heavy rain, snow
- **Heavy Precipitation**: >10 mm/h rainfall

#### Impact Assessment
- Color-coded alerts for different hazard levels
- Recommendations for flight operations
- Integration with route planning (planned feature)

## Demo Mode vs Live Data

### Demo Mode
- **Activated when**: No API credentials configured
- **Features**: All core functionality works with synthetic data
- **Benefits**: Test the system without API dependencies
- **Limitations**: No real flight data

### Live Data Mode
- **Activated when**: API credentials properly configured
- **Features**: Real flight and weather data
- **Benefits**: Actual air traffic monitoring
- **Limitations**: API rate limits apply

## Troubleshooting

### Common Issues

#### "No flights detected"
- **Cause**: API rate limits or network issues
- **Solution**: Wait a few minutes and refresh, or check internet connection

#### "Configuration warnings"
- **Cause**: Missing API credentials
- **Solution**: Add credentials to .env file or use demo mode

#### "Model not trained"
- **Cause**: Collision avoidance model needs training
- **Solution**: Go to Collision Avoidance module and click "Train Model"

#### Slow performance
- **Cause**: Large number of aircraft or limited system resources
- **Solution**: 
  - Select smaller airport regions
  - Close other applications
  - Restart the dashboard

### Error Messages

#### "Import errors" when starting
- **Cause**: Missing Python packages
- **Solution**: Run `pip install -r requirements.txt`

#### "Port already in use"
- **Cause**: Another Streamlit app is running
- **Solution**: Close other Streamlit apps or use `streamlit run dashboard/main.py --server.port 8502`

#### "API connection failed"
- **Cause**: Network issues or invalid credentials
- **Solution**: Check internet connection and verify API credentials

## Performance Tips

### Optimizing Performance
1. **Select specific airports** instead of global monitoring
2. **Use auto-refresh sparingly** to reduce API calls
3. **Close unused browser tabs**
4. **Restart dashboard periodically** for best performance

### System Requirements
- **Minimum**: 4GB RAM, Python 3.8+
- **Recommended**: 8GB RAM, Python 3.9+, broadband internet

## Advanced Features

### Keyboard Shortcuts
- **Ctrl+R**: Refresh current page
- **Ctrl+W**: Close browser tab
- **F5**: Refresh browser page

### URL Parameters
You can bookmark specific configurations:
- `?airport=LAX` - Start with LAX selected
- `?refresh=true` - Start with auto-refresh enabled

### Data Export
- Flight data tables can be copied using standard browser selection
- Screenshots can be taken for reporting purposes

## Support and Updates

### Getting Help
1. Check this user manual first
2. Review error messages in the sidebar
3. Try refreshing or restarting the application
4. Check the technical documentation for advanced issues

### System Updates
- The system uses standard Python packages that update automatically
- API endpoints are stable but may occasionally change
- Monitor console output for important messages

## Best Practices

### For Air Traffic Monitoring
1. **Monitor conflicts regularly** - Check the collision avoidance module frequently
2. **Plan ahead** - Use runway scheduling to prevent bottlenecks
3. **Consider weather** - Check weather conditions before major operations
4. **Maintain situational awareness** - Keep the main dashboard visible

### For System Administration
1. **Regular testing** - Run `python test_system.py` periodically
2. **Monitor API usage** - Stay within rate limits
3. **Keep credentials secure** - Never share API keys
4. **Update dependencies** - Run `pip install -r requirements.txt --upgrade` monthly

## Frequently Asked Questions

**Q: Is this system certified for real air traffic control?**
A: No, this is an educational and demonstration system. It should not be used for actual air traffic control operations.

**Q: How accurate are the conflict predictions?**
A: The system targets >85% accuracy with synthetic training data. Real-world performance may vary.

**Q: Can I use this with other airports?**
A: Yes, the system includes major international airports and can be configured for any location with coordinates.

**Q: How often is the data updated?**
A: Live data updates every 30 seconds with auto-refresh, or manually with the refresh button.

**Q: What happens if I exceed API rate limits?**
A: The system will display a warning and fall back to cached data or demo mode temporarily.

**Q: Can multiple people use this simultaneously?**
A: The current version is designed for single-user operation. Each instance requires its own API credentials.
