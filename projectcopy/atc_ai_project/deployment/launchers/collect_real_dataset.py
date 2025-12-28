#!/usr/bin/env python3
"""
Real Flight Dataset Collection Script
Fetches real flight data from OpenSky Network API and saves to CSV for ML training
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.real_dataset_loader import RealFlightDatasetLoader
from utils.config import Config


def collect_single_snapshot(region: str = 'USA', output_dir: str = 'data/snapshots'):
    """
    Collect a single snapshot of current flights
    
    Args:
        region: Region to collect data from
        output_dir: Directory to save the snapshot
    """
    print(f"\n{'='*70}")
    print("COLLECTING FLIGHT DATA SNAPSHOT")
    print(f"{'='*70}\n")
    
    loader = RealFlightDatasetLoader()
    
    # Fetch live flights
    flights = loader.fetch_live_flights(region=region, limit=200)
    
    if not flights:
        print("❌ No flights collected. Check your API credentials or internet connection.")
        return
    
    # Save to CSV
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_file = output_path / f"flights_{region}_{timestamp}.csv"
    
    loader._save_flights_to_csv(flights, csv_file)
    
    print(f"\n✅ Snapshot collected successfully!")
    print(f"   Region: {region}")
    print(f"   Flights: {len(flights)}")
    print(f"   Saved to: {csv_file}")


def collect_historical(duration_hours: int = 24, interval_minutes: int = 30, region: str = 'USA'):
    """
    Collect historical flight data over time
    
    Args:
        duration_hours: How many hours to collect data
        interval_minutes: Minutes between each collection
        region: Region to monitor
    """
    print(f"\n{'='*70}")
    print("COLLECTING HISTORICAL FLIGHT DATA")
    print(f"{'='*70}")
    print(f"Duration: {duration_hours} hours")
    print(f"Interval: {interval_minutes} minutes")
    print(f"Region: {region}")
    print(f"{'='*70}\n")
    
    loader = RealFlightDatasetLoader()
    flights = loader.collect_historical_data(
        duration_hours=duration_hours,
        interval_minutes=interval_minutes,
        region=region
    )
    
    print(f"\n✅ Historical collection completed!")
    print(f"   Total flights: {len(flights)}")


def create_training_dataset(num_samples: int = 5000, use_live: bool = True, output_file: str = None):
    """
    Create a training dataset from real flight data
    
    Args:
        num_samples: Number of training samples to generate
        use_live: Whether to fetch live data
        output_file: Optional file to save the dataset
    """
    print(f"\n{'='*70}")
    print("CREATING TRAINING DATASET FROM REAL FLIGHT DATA")
    print(f"{'='*70}\n")
    
    loader = RealFlightDatasetLoader()
    X, y = loader.create_training_dataset(
        num_samples=num_samples,
        use_live=use_live,
        use_csv=True
    )
    
    if output_file:
        import pickle
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'wb') as f:
            pickle.dump({'X': X, 'y': y, 'timestamp': datetime.now()}, f)
        
        print(f"\n💾 Dataset saved to: {output_path}")
    
    print(f"\n✅ Training dataset created!")
    print(f"   Samples: {len(X)}")
    print(f"   Features: {X.shape[1]}")
    print(f"   Conflicts: {sum(y)} ({sum(y)/len(y)*100:.1f}%)")


def test_api_connection():
    """Test connection to OpenSky Network API"""
    print(f"\n{'='*70}")
    print("TESTING API CONNECTION")
    print(f"{'='*70}\n")
    
    from utils.api_client import OpenSkyAPI
    
    api = OpenSkyAPI()
    
    print("Testing OpenSky Network API...")
    print(f"Base URL: {api.base_url}")
    print(f"Authentication: {'Configured' if api.client_id else 'Not configured (anonymous)'}")
    
    print("\nFetching sample data...")
    data = api.get_states(bbox=[24.0, 50.0, -125.0, -65.0])  # USA
    
    if data and 'states' in data:
        num_flights = len(data['states'])
        print(f"✅ API connection successful!")
        print(f"   Retrieved: {num_flights} flights")
        
        if num_flights > 0:
            print(f"\n📊 Sample flight data:")
            state = data['states'][0]
            print(f"   ICAO24: {state[0]}")
            print(f"   Callsign: {state[1]}")
            print(f"   Country: {state[2]}")
            print(f"   Position: ({state[6]:.2f}, {state[5]:.2f})")
            print(f"   Altitude: {state[7]} ft")
            print(f"   Velocity: {state[9]} kt")
    else:
        print("❌ API connection failed or returned no data")
        print("💡 Tips:")
        print("   - Check your internet connection")
        print("   - Verify API credentials in .env file")
        print("   - OpenSky free tier has rate limits (400 requests/day)")


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description='Collect real flight data for ATC AI training',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test API connection
  python collect_real_dataset.py test
  
  # Collect a single snapshot
  python collect_real_dataset.py snapshot --region USA
  
  # Collect historical data for 2 hours
  python collect_real_dataset.py historical --duration 2 --interval 15
  
  # Create training dataset
  python collect_real_dataset.py train --samples 5000 --output data/training_data.pkl
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Test command
    subparsers.add_parser('test', help='Test API connection')
    
    # Snapshot command
    snapshot_parser = subparsers.add_parser('snapshot', help='Collect single snapshot')
    snapshot_parser.add_argument('--region', default='USA', 
                                choices=['USA', 'Europe', 'Asia', 'Global'],
                                help='Region to collect data from')
    snapshot_parser.add_argument('--output', default='data/snapshots',
                                help='Output directory for snapshots')
    
    # Historical command
    historical_parser = subparsers.add_parser('historical', help='Collect historical data')
    historical_parser.add_argument('--duration', type=int, default=24,
                                  help='Duration in hours (default: 24)')
    historical_parser.add_argument('--interval', type=int, default=30,
                                  help='Interval in minutes (default: 30)')
    historical_parser.add_argument('--region', default='USA',
                                  choices=['USA', 'Europe', 'Asia', 'Global'],
                                  help='Region to monitor')
    
    # Train command
    train_parser = subparsers.add_parser('train', help='Create training dataset')
    train_parser.add_argument('--samples', type=int, default=5000,
                             help='Number of training samples (default: 5000)')
    train_parser.add_argument('--no-live', action='store_true',
                             help='Don\'t fetch live data, use CSV only')
    train_parser.add_argument('--output', 
                             help='Output file for dataset (pickle format)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Execute command
    if args.command == 'test':
        test_api_connection()
    
    elif args.command == 'snapshot':
        collect_single_snapshot(region=args.region, output_dir=args.output)
    
    elif args.command == 'historical':
        collect_historical(
            duration_hours=args.duration,
            interval_minutes=args.interval,
            region=args.region
        )
    
    elif args.command == 'train':
        create_training_dataset(
            num_samples=args.samples,
            use_live=not args.no_live,
            output_file=args.output
        )


if __name__ == "__main__":
    main()
