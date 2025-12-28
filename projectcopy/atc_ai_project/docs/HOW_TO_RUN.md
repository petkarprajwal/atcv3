# How to Run the ATC AI Project

This guide provides step-by-step instructions to set up and run your Advanced Air Traffic Control AI System.

## 📋 Prerequisites

- **Python 3.8+** (recommended: Python 3.9 or higher)
- **Git** (for version control)
- **Web browser** (Chrome, Firefox, Edge, Safari)
- **Internet connection** (for real-time data APIs)

## 🚀 Quick Start (Recommended)

### Option 1: Run the Complete System

```powershell
# Navigate to project directory
cd "C:\Users\Petka\Desktop\atc version2\projectcopy\atc_ai_project"

# Install dependencies
pip install -r deployment/configs/requirements.txt
pip install -r requirements_opensky.txt

# Launch the complete ATC system
python launch_atc_system.py
```

### Option 2: Run Dashboard Only (Fastest)

```powershell
# Navigate to project directory
cd "C:\Users\Petka\Desktop\atc version2\projectcopy\atc_ai_project"

# Install minimal dependencies
pip install streamlit plotly folium pandas numpy requests

# Launch dashboard
python launch_dashboard.py
```

## 🔧 Detailed Setup Instructions

### Step 1: Environment Setup

1. **Open PowerShell as Administrator**
2. **Navigate to project directory**:
   ```powershell
   cd "C:\Users\Petka\Desktop\atc version2\projectcopy\atc_ai_project"
   ```

3. **Check Python version**:
   ```powershell
   python --version
   ```
   If Python is not installed, download from [python.org](https://python.org)

### Step 2: Install Dependencies

**Option A: Install All Dependencies (Complete Features)**
```powershell
# Install main requirements
pip install -r deployment/configs/requirements.txt

# Install OpenSky API integration
pip install -r requirements_opensky.txt

# Install additional utilities (optional)
pip install asyncio aiofiles
```

**Option B: Install Minimal Dependencies (Quick Start)**
```powershell
pip install streamlit>=1.28.0 plotly>=5.15.0 folium>=0.14.0 pandas>=2.0.0 numpy>=1.24.0 requests>=2.31.0
```

### Step 3: Configure Credentials (preferred: environment variables)

For security, prefer environment variables or a secrets manager instead of committing `credentials.json`.

1) Local development (recommended): create a `.env` file (gitignored) and copy values from `.env.example`.

Example `.env` variables (do NOT commit this file):

```env
# OpenSky credentials (preferred)
OPENSKY_USERNAME=your_opensky_username
OPENSKY_PASSWORD=your_opensky_password

# Optional: other API keys
GOOGLE_MAPS_API_KEY=your_google_maps_key
OPENWEATHER_API_KEY=your_openweather_key
```

This project will first try to load `OPENSKY_USERNAME` / `OPENSKY_PASSWORD` from the environment. If those are not set, it will fall back to `credentials.json` for backward compatibility.

2) Backward compatibility (existing projects): if you already have `credentials.json`, the project will still read it, but you should migrate to env vars and ensure `credentials.json` is listed in `.gitignore` and removed from version control history if it contained secrets.

3) Production: use a secrets manager (AWS Secrets Manager, Azure Key Vault, or GCP Secret Manager) and inject secrets at runtime via your platform/CI.

Notes:
- Do not commit `.env` or `credentials.json`.
- Use least-privilege API keys and rotate them regularly.

## 🎯 Running the System

### Method 1: Complete ATC System

```powershell
# Launch unified system with all components
python launch_atc_system.py

# Or with specific mode
python launch_atc_system.py --mode demo
python launch_atc_system.py --mode realtime
```

### Method 2: Dashboard Only

```powershell
# Launch web dashboard (fastest startup)
python launch_dashboard.py

# Alternative: Direct Streamlit launch
streamlit run web_dashboard_dual_mode.py
```

### Method 3: Real-time System

```powershell
# Launch real-time ATC system
python launch_atc_system_realtime.py
```

### Method 4: Demo Mode

```powershell
# Launch demo system with sample data
python demo_atc_system.py
```

## 🌐 Accessing the System

Once launched, the system will be available at:
- **Main Dashboard**: http://localhost:8501
- **Admin Panel**: http://localhost:8502 (if available)
- **API Endpoints**: http://localhost:8503 (if available)

The system will automatically open your web browser to the main dashboard.

## 🔍 Available Components

### 1. Web Dashboard (`web_dashboard_dual_mode.py`)
- Interactive flight tracking
- Real-time weather overlay
- Collision detection visualization
- Route optimization display

### 2. OpenSky API Integration
- Real-time aircraft data
- Historical flight analysis
- Airport traffic monitoring

### 3. Weather Integration
- Real-time weather data
- Weather impact analysis
- Route weather optimization

### 4. AI Models
- Collision avoidance algorithms
- Trajectory prediction
- Route optimization

## 🧪 Testing the System

```powershell
# Run basic tests
python test_dual_mode.py

# Run OpenSky integration tests
python test_opensky_safe.py

# Run weather integration tests
python test_openweathermap_safe.py

# Run all tests
python -m pytest tests/ -v
```

## 📊 Usage Examples

### Example 1: Run OpenSky Examples
```powershell
python examples/opensky_examples.py
```

### Example 2: Test API Integration
```powershell
python test_opensky.py
```

### Example 3: Demo Flight Simulation
```powershell
python demo_atc_system.py
```

## 🛠️ Troubleshooting

### Common Issues and Solutions

#### 1. **Module Import Errors**
```powershell
# Fix: Install missing dependencies
pip install <missing_module>

# Or reinstall all requirements
pip install -r deployment/configs/requirements.txt --force-reinstall
```

#### 2. **Port Already in Use**
```powershell
# Fix: Use different port
streamlit run web_dashboard_dual_mode.py --server.port 8502
```

#### 3. **API Authentication Errors**
- Check `credentials.json` is properly formatted
- Verify API credentials are valid
- Ensure internet connection is active

#### 4. **Streamlit Launch Issues**
```powershell
# Clear Streamlit cache
streamlit cache clear

# Update Streamlit
pip install --upgrade streamlit
```

## 🎛️ Configuration Options

### Environment Variables
Create a `.env` file for custom configuration:
```env
STREAMLIT_SERVER_PORT=8501
API_TIMEOUT=30
DEBUG_MODE=false
CACHE_ENABLED=true
```

### System Modes
- **DEMO**: Uses sample data, perfect for presentations
- **REALTIME**: Uses live API data
- **TESTING**: Uses test data for development

## 📁 Project Structure Overview

```
atc_ai_project/
├── launch_atc_system.py          # Main system launcher
├── launch_dashboard.py           # Dashboard launcher
├── web_dashboard_dual_mode.py    # Main web interface
├── demo_atc_system.py           # Demo mode
├── credentials.json             # API credentials
├── deployment/configs/          # Configuration files
├── examples/                    # Usage examples
├── tests/                       # Test files
├── docs/                        # Documentation
└── requirements*.txt            # Dependencies
```

## 🚀 Recommended Startup Sequence

1. **For Demo/Presentation**:
   ```powershell
   python launch_dashboard.py
   ```

2. **For Development**:
   ```powershell
   python demo_atc_system.py
   ```

3. **For Production**:
   ```powershell
   python launch_atc_system.py --mode realtime
   ```

## 📞 Support

If you encounter issues:
1. Check this guide first
2. Review error messages in the console
3. Check log files in `deployment/configs/`
4. Verify all dependencies are installed
5. Ensure Python version compatibility

## 🎉 Success Indicators

When the system is running correctly, you should see:
- ✅ Streamlit dashboard loads at http://localhost:8501
- ✅ Flight data appears on the map
- ✅ No error messages in console
- ✅ Interactive controls respond properly
- ✅ Real-time updates (if using live data)

---

**Happy Flying! ✈️**

*The ATC AI System is now ready for air traffic control operations.*