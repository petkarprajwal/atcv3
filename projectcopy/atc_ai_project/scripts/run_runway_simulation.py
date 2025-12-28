"""
Run Runway Scheduling Simulation and Training

This script provides a command-line interface to run the runway scheduling simulation,
train the reinforcement learning model, and compare the performance of different schedulers.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
import matplotlib.pyplot as plt
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('runway_simulation_runner')

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from models.runway_simulation import AirportSimulator, run_training_and_evaluation
    from models.runway_scheduler import RunwayScheduler
    from models.rl_runway_scheduler import ReinforcementScheduler, get_runway_scheduler
    from utils.enhanced_data_processing import process_sample_flights_for_scheduling
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    print(f"Error: {e}")
    sys.exit(1)

def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(description='Runway Scheduling Simulation and Training')
    
    # Main command options
    command_group = parser.add_mutually_exclusive_group(required=True)
    command_group.add_argument('--simulate', action='store_true',
                              help='Run simulation with existing scheduler')
    command_group.add_argument('--train', action='store_true',
                              help='Train new RL scheduler model')
    command_group.add_argument('--compare', action='store_true',
                              help='Compare standard and RL schedulers')
    
    # Simulation parameters
    parser.add_argument('--runways', type=int, default=2,
                       help='Number of runways to simulate (default: 2)')
    parser.add_argument('--duration', type=float, default=24.0,
                       help='Simulation duration in hours (default: 24.0)')
    parser.add_argument('--step', type=float, default=15.0,
                       help='Simulation time step in minutes (default: 15.0)')
    parser.add_argument('--airport', type=str, default='SIM',
                       help='Airport code for simulation (default: SIM)')
    
    # Training parameters
    parser.add_argument('--episodes', type=int, default=50,
                       help='Number of training episodes for RL (default: 50)')
    parser.add_argument('--model-path', type=str, default='data/models/rl_runway_scheduler.h5',
                       help='Path to save/load RL model (default: data/models/rl_runway_scheduler.h5)')
    
    # Output options
    parser.add_argument('--no-plot', action='store_true',
                       help='Disable plotting of results')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose output')
    
    return parser.parse_args()

def ensure_directory_exists(file_path):
    """Ensure the directory for a file exists"""
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)

def run_simulation(args):
    """Run simulation with existing scheduler"""
    logger.info(f"Running simulation with {args.runways} runways for {args.duration} hours")
    
    # Determine if we should use RL
    use_rl = os.path.exists(args.model_path)
    
    # Create simulator
    simulator = AirportSimulator(
        airport_code=args.airport,
        num_runways=args.runways,
        use_reinforcement_learning=use_rl,
        model_path=args.model_path if use_rl else None
    )
    
    # Run simulation
    results = simulator.run_simulation(
        duration_hours=args.duration,
        time_step_minutes=args.step
    )
    
    # Plot results unless disabled
    if not args.no_plot:
        simulator.plot_simulation_results(results)
    
    # Print summary
    print("\nSimulation Results Summary:")
    print(f"Total Flights: {results['total_flights_generated']}")
    print(f"Emergencies: {results['emergencies_generated']}")
    print(f"Average Delay: {results['metrics']['average_delay']:.1f} minutes")
    print(f"Runway Utilization: {results['metrics']['runway_utilization']:.1f}%")
    print(f"On-time Percentage: {results['metrics']['on_time_percentage']:.1f}%")
    
    return results

def train_model(args):
    """Train a new RL scheduler model"""
    logger.info(f"Training RL scheduler with {args.episodes} episodes")
    
    # Ensure model directory exists
    ensure_directory_exists(args.model_path)
    
    # Run training and evaluation
    comparison = run_training_and_evaluation(
        num_runways=args.runways,
        training_episodes=args.episodes,
        save_path=args.model_path
    )
    
    # Print summary
    if 'improvements' in comparison:
        print("\nTraining Results Summary:")
        print(f"Model saved to: {args.model_path}")
        print(f"Delay Improvement: {comparison['improvements'].get('average_delay', 0):.1f}%")
        print(f"Utilization Improvement: {comparison['improvements'].get('runway_utilization', 0):.1f}%")
    
    return comparison

def compare_schedulers(args):
    """Compare standard and RL schedulers"""
    logger.info("Comparing standard and RL schedulers")
    
    # Check if model exists
    if not os.path.exists(args.model_path):
        logger.error(f"RL model not found at {args.model_path}")
        print(f"Error: RL model not found at {args.model_path}")
        print("Please train a model first using the --train option")
        sys.exit(1)
    
    # Create simulator with standard scheduler
    simulator = AirportSimulator(
        airport_code=args.airport,
        num_runways=args.runways,
        use_reinforcement_learning=False
    )
    
    # Create RL scheduler
    base_scheduler = RunwayScheduler()
    for i in range(args.runways):
        base_scheduler.add_runway(f"RWY{i+1:02d}", 30)
    
    rl_scheduler = ReinforcementScheduler(base_scheduler)
    rl_scheduler.load_model(args.model_path)
    
    # Run comparison
    comparison = simulator.compare_schedulers(
        duration_hours=args.duration,
        standard_scheduler=None,  # Will use the one already in simulator
        rl_scheduler=rl_scheduler
    )
    
    # Plot comparison results unless disabled
    if not args.no_plot:
        simulator.plot_comparison_results(comparison)
    
    # Print summary
    print("\nScheduler Comparison Summary:")
    if 'improvements' in comparison:
        print(f"Standard Delay: {comparison['standard_scheduler']['average_delay']:.1f} minutes")
        print(f"RL Delay: {comparison['rl_scheduler']['average_delay']:.1f} minutes")
        print(f"Delay Improvement: {comparison['improvements'].get('average_delay', 0):.1f}%")
        print(f"Utilization Improvement: {comparison['improvements'].get('runway_utilization', 0):.1f}%")
    
    return comparison

def main():
    """Main function"""
    # Parse arguments
    args = parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        if args.simulate:
            run_simulation(args)
        elif args.train:
            train_model(args)
        elif args.compare:
            compare_schedulers(args)
    except Exception as e:
        logger.error(f"Error in simulation: {e}", exc_info=True)
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()