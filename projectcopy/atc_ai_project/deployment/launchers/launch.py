#!/usr/bin/env python3
"""
Unified ATC Dashboard Launcher
Launches the appropriate dashboard based on command line arguments
"""

import sys
import subprocess
import socket
import webbrowser
import os
from pathlib import Path
import argparse

def check_port(port, host='localhost'):
    """Check if a port is available"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex((host, port))
            return result == 0
    except:
        return False

def find_available_port(start_port=8501):
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + 10):
        if not check_port(port):
            return port
    return None

def launch_dashboard(dashboard_type="realtime", port=None, headless=False):
    """Launch the specified dashboard type"""
    
    project_dir = Path(__file__).parent
    
    # Dashboard file mapping
    dashboard_files = {
        "realtime": "dashboard/realtime_main.py",
        "enhanced": "dashboard/enhanced_dashboard.py", 
        "secure": "dashboard/secure_dashboard.py",
        "main": "dashboard/main.py"
    }
    
    if dashboard_type not in dashboard_files:
        print(f"❌ Unknown dashboard type: {dashboard_type}")
        print(f"Available types: {', '.join(dashboard_files.keys())}")
        return False
    
    dashboard_file = project_dir / dashboard_files[dashboard_type]
    
    if not dashboard_file.exists():
        print(f"❌ Dashboard file not found: {dashboard_file}")
        return False
    
    # Find available port
    if port is None:
        port = find_available_port()
        if port is None:
            print("❌ No available ports found (8501-8511)")
            return False
    
    print(f"🚀 Launching {dashboard_type} dashboard on port {port}")
    print(f"📁 Dashboard: {dashboard_file}")
    print(f"🌐 URL: http://localhost:{port}")
    
    # Build command
    cmd = [
        sys.executable, "-m", "streamlit", "run", 
        str(dashboard_file),
        "--server.port", str(port)
    ]
    
    if headless:
        cmd.append("--server.headless=true")
    
    try:
        # Launch streamlit
        subprocess.run(cmd, cwd=str(project_dir))
        return True
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped by user")
        return True
    except FileNotFoundError:
        print("❌ Streamlit not found. Install with: pip install streamlit")
        return False
    except Exception as e:
        print(f"❌ Error launching dashboard: {e}")
        return False

def main():
    """Main function with argument parsing"""
    parser = argparse.ArgumentParser(description="Launch ATC AI Dashboard")
    parser.add_argument("--type", "-t", 
                       choices=["realtime", "enhanced", "secure", "main"],
                       default="realtime",
                       help="Dashboard type to launch (default: realtime)")
    parser.add_argument("--port", "-p", type=int,
                       help="Port to use (default: auto-detect)")
    parser.add_argument("--headless", action="store_true",
                       help="Run in headless mode")
    parser.add_argument("--test", action="store_true",
                       help="Test system before launching")
    
    args = parser.parse_args()
    
    print("🚀 ATC AI Dashboard Launcher")
    print("=" * 50)
    
    # Test system if requested
    if args.test:
        print("🧪 Testing system...")
        try:
            result = subprocess.run([sys.executable, "test_enhanced_system.py"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ System test passed")
            else:
                print("⚠️ System test failed, but continuing...")
        except:
            print("⚠️ Could not run system test, but continuing...")
    
    # Launch dashboard
    success = launch_dashboard(
        dashboard_type=args.type,
        port=args.port,
        headless=args.headless
    )
    
    if not success:
        print("\n🔧 Troubleshooting Tips:")
        print("1. Install Streamlit: pip install streamlit")
        print("2. Check firewall settings")
        print("3. Try different port: --port 8502")
        print("4. Check antivirus software")
        sys.exit(1)

if __name__ == "__main__":
    main()






