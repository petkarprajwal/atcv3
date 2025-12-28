#!/usr/bin/env python3
"""
ATC AI Dashboard Launcher
Simple launcher for the web dashboard
"""

import sys
import os
import webbrowser
import time
import threading

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web_dashboard_dual_mode import ATCWebDashboard

def launch_dashboard():
    """Launch the ATC AI Dashboard"""
    
    print("ATC AI Dashboard Launcher")
    print("="*40)
    
    # Initialize dashboard
    dashboard = ATCWebDashboard()
    
    # Start in DEMO mode (perfect for presentations)
    dashboard.set_mode("DEMO")
    dashboard.start_dashboard()
    
    print("\nDashboard Status:")
    print("- Mode: DEMO (perfect for presentations)")
    print("- URL: http://localhost:5000")
    print("- Features: Flight tracking, weather, airport status, safety alerts")
    print("- Toggle: Click the switch to change between DEMO and REAL-TIME modes")
    
    # Open browser automatically
    def open_browser():
        time.sleep(2)  # Wait for server to start
        webbrowser.open('http://localhost:5000')
        print("\nBrowser opened automatically!")
    
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    print("\nStarting web server...")
    print("Press Ctrl+C to stop the dashboard")
    
    try:
        # Run the web server
        dashboard.run_web_server(host='localhost', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\nStopping dashboard...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        dashboard.stop_dashboard()
        print("Dashboard stopped.")

if __name__ == "__main__":
    launch_dashboard()


