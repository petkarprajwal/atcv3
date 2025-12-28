#!/usr/bin/env python3
"""
Phase 3: Real-Time Integration - Master Launcher
Complete real-time integration system with streaming, API, and dashboard
"""

import sys
import os
import subprocess
import time
import threading
import signal
from pathlib import Path
import argparse
import json
import logging
from datetime import datetime
import requests
import webbrowser
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('real_time_integration/phase3_runtime.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Phase3RealTimeIntegration:
    """Master controller for Phase 3 Real-Time Integration"""
    
    def __init__(self, config_file: str = "real_time_integration/phase3_config.json"):
        self.config = self._load_config(config_file)
        self.processes = {}
        self.is_running = False
        self.start_time = None
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _load_config(self, config_file: str) -> Dict:
        """Load Phase 3 configuration"""
        default_config = {
            "components": {
                "data_streaming": {
                    "enabled": True,
                    "port": 8765,
                    "config_file": "real_time_integration/streaming/stream_config.json"
                },
                "rest_api": {
                    "enabled": True,
                    "host": "0.0.0.0",
                    "port": 8000,
                    "reload": True
                },
                "live_dashboard": {
                    "enabled": True,
                    "port": 8501,
                    "host": "localhost"
                }
            },
            "integration": {
                "auto_start_all": True,
                "startup_delay_seconds": 2,
                "health_check_interval": 10,
                "max_startup_wait": 30
            },
            "monitoring": {
                "enable_health_checks": True,
                "enable_performance_monitoring": True,
                "log_level": "INFO"
            }
        }
        
        config_path = Path(config_file)
        if config_path.exists():
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        # Save config for reference
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        return default_config
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down Phase 3...")
        self.stop_all_services()
        sys.exit(0)
    
    def start_data_streaming(self) -> bool:
        """Start data streaming service"""
        try:
            logger.info("Starting data streaming service...")
            
            # Start streaming service
            streaming_script = Path("real_time_integration/streaming/real_time_data_streamer.py")
            if not streaming_script.exists():
                logger.error(f"Streaming script not found: {streaming_script}")
                return False
            
            process = subprocess.Popen([
                sys.executable, str(streaming_script)
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.processes['data_streaming'] = process
            logger.info("Data streaming service started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start data streaming: {e}")
            return False
    
    def start_rest_api(self) -> bool:
        """Start REST API service"""
        try:
            logger.info("Starting REST API service...")
            
            # Start API service
            api_script = Path("real_time_integration/api/rest_api.py")
            if not api_script.exists():
                logger.error(f"API script not found: {api_script}")
                return False
            
            api_config = self.config['components']['rest_api']
            
            process = subprocess.Popen([
                sys.executable, str(api_script)
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.processes['rest_api'] = process
            logger.info(f"REST API service started on {api_config['host']}:{api_config['port']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start REST API: {e}")
            return False
    
    def start_live_dashboard(self) -> bool:
        """Start live dashboard service"""
        try:
            logger.info("Starting live dashboard service...")
            
            # Start dashboard service
            dashboard_script = Path("real_time_integration/dashboard/live_dashboard.py")
            if not dashboard_script.exists():
                logger.error(f"Dashboard script not found: {dashboard_script}")
                return False
            
            dashboard_config = self.config['components']['live_dashboard']
            
            process = subprocess.Popen([
                "streamlit", "run", str(dashboard_script),
                "--server.port", str(dashboard_config['port']),
                "--server.address", dashboard_config['host'],
                "--server.headless", "true"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.processes['live_dashboard'] = process
            logger.info(f"Live dashboard started on {dashboard_config['host']}:{dashboard_config['port']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start live dashboard: {e}")
            return False
    
    def start_all_services(self) -> Dict[str, bool]:
        """Start all Phase 3 services"""
        
        self.start_time = datetime.now()
        self.is_running = True
        
        logger.info("🚀 Starting Phase 3: Real-Time Integration")
        logger.info("=" * 60)
        
        results = {}
        
        # Start services in order
        if self.config['components']['data_streaming']['enabled']:
            results['data_streaming'] = self.start_data_streaming()
            time.sleep(self.config['integration']['startup_delay_seconds'])
        
        if self.config['components']['rest_api']['enabled']:
            results['rest_api'] = self.start_rest_api()
            time.sleep(self.config['integration']['startup_delay_seconds'])
        
        if self.config['components']['live_dashboard']['enabled']:
            results['live_dashboard'] = self.start_live_dashboard()
            time.sleep(self.config['integration']['startup_delay_seconds'])
        
        # Wait for services to start
        self._wait_for_services()
        
        # Start monitoring
        if self.config['monitoring']['enable_health_checks']:
            self._start_health_monitoring()
        
        logger.info("🎉 Phase 3: Real-Time Integration started successfully!")
        self._print_service_status()
        
        return results
    
    def _wait_for_services(self):
        """Wait for services to be ready"""
        
        logger.info("Waiting for services to be ready...")
        
        max_wait = self.config['integration']['max_startup_wait']
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            all_ready = True
            
            # Check API
            if 'rest_api' in self.processes:
                try:
                    response = requests.get("http://localhost:8000/health", timeout=2)
                    if response.status_code != 200:
                        all_ready = False
                except:
                    all_ready = False
            
            if all_ready:
                logger.info("All services are ready!")
                return
            
            time.sleep(1)
        
        logger.warning("Some services may not be fully ready")
    
    def _start_health_monitoring(self):
        """Start health monitoring thread"""
        
        def health_monitor():
            while self.is_running:
                try:
                    self._check_service_health()
                    time.sleep(self.config['integration']['health_check_interval'])
                except Exception as e:
                    logger.error(f"Health monitoring error: {e}")
                    time.sleep(5)
        
        monitor_thread = threading.Thread(target=health_monitor)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        logger.info("Health monitoring started")
    
    def _check_service_health(self):
        """Check health of all services"""
        
        # Check API health
        if 'rest_api' in self.processes:
            try:
                response = requests.get("http://localhost:8000/health", timeout=5)
                if response.status_code == 200:
                    logger.debug("API health check: OK")
                else:
                    logger.warning("API health check: FAILED")
            except:
                logger.warning("API health check: UNAVAILABLE")
        
        # Check process health
        for service_name, process in self.processes.items():
            if process.poll() is not None:
                logger.error(f"Service {service_name} has stopped unexpectedly")
    
    def _print_service_status(self):
        """Print status of all services"""
        
        logger.info("📊 Service Status:")
        logger.info("-" * 40)
        
        # Data Streaming
        if 'data_streaming' in self.processes:
            status = "✅ Running" if self.processes['data_streaming'].poll() is None else "❌ Stopped"
            logger.info(f"Data Streaming: {status}")
        
        # REST API
        if 'rest_api' in self.processes:
            status = "✅ Running" if self.processes['rest_api'].poll() is None else "❌ Stopped"
            api_config = self.config['components']['rest_api']
            logger.info(f"REST API: {status} (http://{api_config['host']}:{api_config['port']})")
        
        # Live Dashboard
        if 'live_dashboard' in self.processes:
            status = "✅ Running" if self.processes['live_dashboard'].poll() is None else "❌ Stopped"
            dashboard_config = self.config['components']['live_dashboard']
            logger.info(f"Live Dashboard: {status} (http://{dashboard_config['host']}:{dashboard_config['port']})")
        
        logger.info("-" * 40)
        logger.info("🌐 Access URLs:")
        logger.info(f"  • API Documentation: http://localhost:8000/docs")
        logger.info(f"  • Live Dashboard: http://localhost:8501")
        logger.info(f"  • WebSocket: ws://localhost:8765/ws/realtime")
    
    def stop_all_services(self):
        """Stop all services"""
        
        logger.info("Stopping all Phase 3 services...")
        self.is_running = False
        
        for service_name, process in self.processes.items():
            try:
                logger.info(f"Stopping {service_name}...")
                process.terminate()
                
                # Wait for graceful shutdown
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning(f"Force killing {service_name}...")
                    process.kill()
                    process.wait()
                
                logger.info(f"{service_name} stopped")
                
            except Exception as e:
                logger.error(f"Error stopping {service_name}: {e}")
        
        self.processes.clear()
        logger.info("All services stopped")
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get status of all services"""
        
        status = {
            "is_running": self.is_running,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
            "services": {}
        }
        
        for service_name, process in self.processes.items():
            status["services"][service_name] = {
                "running": process.poll() is None,
                "pid": process.pid,
                "return_code": process.returncode
            }
        
        return status
    
    def open_dashboard(self):
        """Open dashboard in browser"""
        
        dashboard_config = self.config['components']['live_dashboard']
        dashboard_url = f"http://{dashboard_config['host']}:{dashboard_config['port']}"
        
        try:
            webbrowser.open(dashboard_url)
            logger.info(f"Opened dashboard in browser: {dashboard_url}")
        except Exception as e:
            logger.error(f"Failed to open dashboard: {e}")
            logger.info(f"Please manually open: {dashboard_url}")

def main():
    """Main function for Phase 3 launcher"""
    
    parser = argparse.ArgumentParser(description="Phase 3: Real-Time Integration Launcher")
    parser.add_argument("--config", type=str, default="real_time_integration/phase3_config.json",
                       help="Configuration file path")
    parser.add_argument("--services", nargs="+", 
                       choices=["data_streaming", "rest_api", "live_dashboard"],
                       help="Specific services to start")
    parser.add_argument("--no-dashboard", action="store_true",
                       help="Don't start the live dashboard")
    parser.add_argument("--no-api", action="store_true",
                       help="Don't start the REST API")
    parser.add_argument("--no-streaming", action="store_true",
                       help="Don't start data streaming")
    parser.add_argument("--open-dashboard", action="store_true",
                       help="Open dashboard in browser after starting")
    parser.add_argument("--status", action="store_true",
                       help="Show service status and exit")
    
    args = parser.parse_args()
    
    # Initialize Phase 3 system
    phase3 = Phase3RealTimeIntegration(args.config)
    
    # Handle status command
    if args.status:
        status = phase3.get_service_status()
        print(json.dumps(status, indent=2))
        return
    
    # Update config based on arguments
    if args.no_dashboard:
        phase3.config['components']['live_dashboard']['enabled'] = False
    if args.no_api:
        phase3.config['components']['rest_api']['enabled'] = False
    if args.no_streaming:
        phase3.config['components']['data_streaming']['enabled'] = False
    
    if args.services:
        # Disable all services first
        for service in phase3.config['components']:
            phase3.config['components'][service]['enabled'] = False
        
        # Enable only specified services
        for service in args.services:
            if service in phase3.config['components']:
                phase3.config['components'][service]['enabled'] = True
    
    print("🚀 Phase 3: Real-Time Integration")
    print("=" * 60)
    print("Starting real-time ATC AI system with:")
    
    if phase3.config['components']['data_streaming']['enabled']:
        print("  ✅ Real-Time Data Streaming")
    if phase3.config['components']['rest_api']['enabled']:
        print("  ✅ RESTful API Server")
    if phase3.config['components']['live_dashboard']['enabled']:
        print("  ✅ Live Dashboard")
    
    print("=" * 60)
    
    try:
        # Start all services
        results = phase3.start_all_services()
        
        # Check if all services started successfully
        failed_services = [name for name, success in results.items() if not success]
        if failed_services:
            logger.error(f"Failed to start services: {failed_services}")
            phase3.stop_all_services()
            sys.exit(1)
        
        # Open dashboard if requested
        if args.open_dashboard and phase3.config['components']['live_dashboard']['enabled']:
            time.sleep(3)  # Wait for dashboard to start
            phase3.open_dashboard()
        
        # Keep running
        logger.info("Phase 3 is running. Press Ctrl+C to stop.")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutdown requested by user")
        
    except Exception as e:
        logger.error(f"Phase 3 startup failed: {e}")
        phase3.stop_all_services()
        sys.exit(1)
    
    finally:
        phase3.stop_all_services()

if __name__ == "__main__":
    main()
