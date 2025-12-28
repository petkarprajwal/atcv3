#!/usr/bin/env python3
"""
Phase 1 Data Collection Launcher
Easy-to-use script for collecting all required datasets
"""

import sys
import os
from pathlib import Path
import argparse
import time
from datetime import datetime

# Add data_collection to path
sys.path.append(str(Path(__file__).parent / "data_collection"))

from master_data_collector import MasterDataCollector

def print_banner():
    """Print collection banner"""
    print("=" * 80)
    print("🚀 PHASE 1: DATA FOUNDATION COLLECTION")
    print("=" * 80)
    print("This script will collect comprehensive datasets for your ATC AI system:")
    print("  • Historical Flight Data (6 months)")
    print("  • Weather Historical Data (2 years)")
    print("  • Airport Operations Data (1 year)")
    print("=" * 80)

def print_progress(current, total, message):
    """Print progress indicator"""
    percentage = (current / total) * 100
    bar_length = 40
    filled_length = int(bar_length * current // total)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    print(f'\r[{bar}] {percentage:.1f}% - {message}', end='', flush=True)

def main():
    """Main collection function"""
    parser = argparse.ArgumentParser(description="Phase 1 Data Collection")
    parser.add_argument("--mode", choices=["full", "quick", "demo"], default="full",
                       help="Collection mode: full (production), quick (testing), demo (minimal)")
    parser.add_argument("--flight-days", type=int, default=180,
                       help="Flight data duration in days (default: 180)")
    parser.add_argument("--weather-days", type=int, default=730,
                       help="Weather data duration in days (default: 730)")
    parser.add_argument("--airport-days", type=int, default=365,
                       help="Airport data duration in days (default: 365)")
    parser.add_argument("--output-dir", type=str, default="data_collection/historical_data",
                       help="Output directory for collected data")
    
    args = parser.parse_args()
    
    # Print banner
    print_banner()
    
    # Set collection parameters based on mode
    if args.mode == "demo":
        flight_days = 7
        weather_days = 30
        airport_days = 7
        print("🎯 DEMO MODE: Collecting minimal data for demonstration")
    elif args.mode == "quick":
        flight_days = 30
        weather_days = 90
        airport_days = 30
        print("⚡ QUICK MODE: Collecting reduced data for testing")
    else:
        flight_days = args.flight_days
        weather_days = args.weather_days
        airport_days = args.airport_days
        print("🚀 FULL MODE: Collecting comprehensive production data")
    
    print(f"📊 Collection Plan:")
    print(f"  • Flight Data: {flight_days} days")
    print(f"  • Weather Data: {weather_days} days")
    print(f"  • Airport Data: {airport_days} days")
    print(f"  • Output Directory: {args.output_dir}")
    
    # Confirm before starting
    if args.mode == "full":
        response = input("\n⚠️ This will collect large amounts of data. Continue? (y/N): ")
        if response.lower() != 'y':
            print("❌ Collection cancelled by user")
            return
    
    print(f"\n🚀 Starting data collection at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Initialize master collector
    try:
        collector = MasterDataCollector()
        
        # Update configuration
        collector.config['collection_plan']['flight_data']['duration_days'] = flight_days
        collector.config['collection_plan']['weather_data']['duration_days'] = weather_days
        collector.config['collection_plan']['airport_data']['duration_days'] = airport_days
        collector.config['output']['base_directory'] = args.output_dir
        
        # Start collection
        start_time = time.time()
        results = collector.run_complete_collection()
        end_time = time.time()
        
        # Print final results
        print("\n" + "=" * 80)
        print("🎉 PHASE 1 DATA COLLECTION COMPLETED!")
        print("=" * 80)
        
        total_duration = (end_time - start_time) / 60
        successful_collections = sum(1 for r in results.values() if r['success'])
        total_records = sum(r['stats'].total_records for r in results.values() if r['success'])
        
        print(f"⏱️ Total Duration: {total_duration:.1f} minutes")
        print(f"✅ Successful Collections: {successful_collections}/{len(results)}")
        print(f"📊 Total Records Collected: {total_records:,}")
        
        print(f"\n📋 Collection Results:")
        for collection_type, result in results.items():
            if result['success']:
                stats = result['stats']
                print(f"  ✅ {collection_type.replace('_', ' ').title()}: {stats.total_records:,} records ({stats.data_quality_score:.1f}% quality)")
            else:
                print(f"  ❌ {collection_type.replace('_', ' ').title()}: Failed - {result['error']}")
        
        print(f"\n📁 Generated Files:")
        print(f"  • {args.output_dir}/master_collection_report.json")
        print(f"  • {args.output_dir}/collection_summary.csv")
        print(f"  • {args.output_dir}/flight_data.db")
        print(f"  • {args.output_dir}/weather_data.db")
        print(f"  • {args.output_dir}/airport_data.db")
        
        print(f"\n🎤 Presentation Ready Statistics:")
        print(f"  • Total Datasets: {len(results)}")
        print(f"  • Data Records: {total_records:,}")
        print(f"  • Collection Time: {total_duration:.1f} minutes")
        print(f"  • Success Rate: {successful_collections/len(results)*100:.1f}%")
        
        print(f"\n🚀 Next Steps:")
        print(f"  1. Review collection reports in {args.output_dir}/")
        print(f"  2. Use data for AI model training")
        print(f"  3. Proceed to Phase 2: Advanced AI Models")
        
        print("=" * 80)
        
    except KeyboardInterrupt:
        print("\n❌ Collection interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Collection failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
