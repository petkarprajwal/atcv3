"""
Performance evaluation and visualization tools for the ATC system.
Generates metrics, graphs, and analysis reports.
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict, Tuple
import pandas as pd
from datetime import datetime
import time

class PerformanceEvaluator:
    """Evaluates and visualizes system performance"""
    
    def __init__(self):
        self.metrics = {
            'detection_rates': [],
            'resolution_times': [],
            'false_positives': [],
            'computational_time': []
        }
        
        # Style configuration
        plt.style.use('seaborn')
        self.colors = sns.color_palette("husl", 8)
    
    def record_detection_event(self, 
                             true_conflicts: int,
                             detected_conflicts: int,
                             false_positives: int,
                             computation_time: float):
        """Record a detection cycle's performance metrics"""
        if true_conflicts > 0:
            detection_rate = detected_conflicts / true_conflicts
        else:
            detection_rate = 1.0 if detected_conflicts == 0 else 0.0
            
        self.metrics['detection_rates'].append(detection_rate)
        self.metrics['false_positives'].append(false_positives)
        self.metrics['computational_time'].append(computation_time)
    
    def record_resolution(self, 
                         resolution_time: float,
                         success: bool,
                         scenario_type: str):
        """Record resolution attempt metrics"""
        self.metrics['resolution_times'].append({
            'time': resolution_time,
            'success': success,
            'type': scenario_type
        })
    
    def plot_detection_performance(self, save_path: str = None):
        """Generate detection performance plot"""
        plt.figure(figsize=(10, 6))
        
        # Plot detection rate over time
        rates = self.metrics['detection_rates']
        x = range(len(rates))
        
        plt.plot(x, rates, 'b-', label='Detection Rate', color=self.colors[0])
        plt.fill_between(x, rates, alpha=0.3, color=self.colors[0])
        
        plt.title('Conflict Detection Performance Over Time')
        plt.xlabel('Detection Cycle')
        plt.ylabel('Detection Rate')
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        if save_path:
            plt.savefig(save_path)
            plt.close()
        else:
            plt.show()
    
    def plot_resolution_metrics(self, save_path: str = None):
        """Generate resolution performance plots"""
        # Convert resolution data to DataFrame
        df = pd.DataFrame(self.metrics['resolution_times'])
        
        # Create subplot grid
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Plot 1: Resolution time distribution
        sns.boxplot(data=df, x='type', y='time', ax=ax1)
        ax1.set_title('Resolution Time by Scenario Type')
        ax1.set_xlabel('Scenario Type')
        ax1.set_ylabel('Resolution Time (seconds)')
        
        # Plot 2: Success rate by type
        success_rates = df.groupby('type')['success'].mean()
        success_rates.plot(kind='bar', ax=ax2, color=self.colors)
        ax2.set_title('Resolution Success Rate by Scenario Type')
        ax2.set_xlabel('Scenario Type')
        ax2.set_ylabel('Success Rate')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path)
            plt.close()
        else:
            plt.show()
    
    def plot_computational_performance(self, save_path: str = None):
        """Generate computational performance metrics"""
        comp_times = self.metrics['computational_time']
        
        plt.figure(figsize=(10, 6))
        
        # Plot computation time trend
        plt.plot(comp_times, 'g-', label='Computation Time', color=self.colors[2])
        
        # Add moving average
        window = min(50, len(comp_times))
        if window > 0:
            moving_avg = pd.Series(comp_times).rolling(window=window).mean()
            plt.plot(moving_avg, 'r-', label=f'{window}-point Moving Average',
                    color=self.colors[3])
        
        plt.title('System Computational Performance')
        plt.xlabel('Update Cycle')
        plt.ylabel('Computation Time (seconds)')
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        if save_path:
            plt.savefig(save_path)
            plt.close()
        else:
            plt.show()
    
    def generate_performance_report(self) -> Dict:
        """Generate comprehensive performance report"""
        df_resolutions = pd.DataFrame(self.metrics['resolution_times'])
        
        report = {
            'detection': {
                'average_rate': np.mean(self.metrics['detection_rates']),
                'std_dev': np.std(self.metrics['detection_rates']),
                'false_positive_rate': np.mean(self.metrics['false_positives'])
            },
            'resolution': {
                'overall_success_rate': df_resolutions['success'].mean(),
                'average_time': df_resolutions['time'].mean(),
                'by_type': df_resolutions.groupby('type').agg({
                    'success': 'mean',
                    'time': ['mean', 'std']
                }).to_dict()
            },
            'computational': {
                'average_time': np.mean(self.metrics['computational_time']),
                'max_time': np.max(self.metrics['computational_time']),
                '95th_percentile': np.percentile(self.metrics['computational_time'], 95)
            }
        }
        
        return report

def run_performance_evaluation(num_cycles: int = 1000):
    """
    Run a simulation to generate performance metrics
    
    Args:
        num_cycles: Number of evaluation cycles to run
    """
    evaluator = PerformanceEvaluator()
    
    # Simulate detection cycles
    for _ in range(num_cycles):
        # Simulate detection performance
        true_conflicts = np.random.poisson(2)  # Random number of true conflicts
        detected = np.random.binomial(true_conflicts, 0.95)  # 95% detection rate
        false_pos = np.random.poisson(0.1)  # Random false positives
        comp_time = np.random.normal(0.15, 0.03)  # Random computation time
        
        evaluator.record_detection_event(
            true_conflicts, detected, false_pos, comp_time
        )
        
        # Simulate resolutions for each detected conflict
        for _ in range(detected):
            scenario = np.random.choice(['Head-on', 'Crossing', 'Overtaking'])
            success = np.random.random() > 0.02  # 98% success rate
            res_time = np.random.normal(45, 10)  # Random resolution time
            
            evaluator.record_resolution(res_time, success, scenario)
    
    # Generate plots
    evaluator.plot_detection_performance('detection_performance.png')
    evaluator.plot_resolution_metrics('resolution_metrics.png')
    evaluator.plot_computational_performance('computational_performance.png')
    
    # Generate report
    report = evaluator.generate_performance_report()
    
    return report

if __name__ == "__main__":
    # Run evaluation
    report = run_performance_evaluation()
    
    # Print summary
    print("\nPerformance Evaluation Summary")
    print("==============================")
    print(f"Average Detection Rate: {report['detection']['average_rate']:.3f}")
    print(f"Overall Resolution Success: {report['resolution']['overall_success_rate']:.3f}")
    print(f"Average Computation Time: {report['computational']['average_time']*1000:.2f}ms")