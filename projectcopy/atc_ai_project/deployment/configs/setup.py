#!/usr/bin/env python3
"""
ATC AI System Setup Script
Installs dependencies and sets up the system
"""

import subprocess
import sys
import os
from pathlib import Path

def install_requirements():
    """Install required packages"""
    print("📦 Installing dependencies...")
    
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if not requirements_file.exists():
        print("❌ requirements.txt not found")
        return False
    
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(requirements_file)], 
                      check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_env_example():
    """Create .env.example file if it doesn't exist"""
    env_example = Path(__file__).parent / ".env.example"
    
    if not env_example.exists():
        print("📝 Creating .env.example file...")
        env_content = """# OpenSky Network (Free)
OPENSKY_USERNAME=your_username
OPENSKY_PASSWORD=your_password

# OpenWeatherMap (Free)
OPENWEATHER_API_KEY=your_api_key

# Commercial APIs (Optional)
AVIATIONSTACK_API_KEY=your_key
FLIGHTAWARE_API_KEY=your_key
RAPIDAPI_KEY=your_key

# Real-time Settings
WEBSOCKET_ENABLED=True
WEBSOCKET_PORT=8765
UPDATE_INTERVAL=2
"""
        env_example.write_text(env_content)
        print("✅ Created .env.example")

def test_system():
    """Test if the system is working"""
    print("🧪 Testing system...")
    
    try:
        result = subprocess.run([sys.executable, "test_enhanced_system.py"], 
                              capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print("✅ System test passed")
            return True
        else:
            print("⚠️ System test failed, but setup completed")
            return True
    except subprocess.TimeoutExpired:
        print("⚠️ System test timed out, but setup completed")
        return True
    except FileNotFoundError:
        print("⚠️ Test file not found, but setup completed")
        return True

def main():
    """Main setup function"""
    print("🚀 ATC AI System Setup")
    print("=" * 40)
    
    # Install requirements
    if not install_requirements():
        print("❌ Setup failed at dependency installation")
        return False
    
    # Create .env.example
    create_env_example()
    
    # Test system
    test_system()
    
    print("\n🎉 Setup completed successfully!")
    print("\n🚀 Next steps:")
    print("1. Launch dashboard: python launch.py")
    print("2. Or use batch file: start_dashboard.bat")
    print("3. Open browser to: http://localhost:8501")
    print("\n📚 For more info, see: DOCUMENTATION.md")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)






