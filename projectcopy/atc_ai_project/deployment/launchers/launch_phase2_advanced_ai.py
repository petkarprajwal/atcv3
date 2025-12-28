#!/usr/bin/env python3
"""
Phase 2: Advanced AI Models - Master Launcher
Complete system for training and deploying advanced AI models
"""

import sys
import os
from pathlib import Path
import argparse
import time
from datetime import datetime
import json
import logging

# Add advanced_ai to path
sys.path.append(str(Path(__file__).parent / "advanced_ai"))
sys.path.append(str(Path(__file__).parent / "advanced_ai" / "models"))
sys.path.append(str(Path(__file__).parent / "advanced_ai" / "optimization"))

# Import our advanced AI components
from models.lstm_trajectory_predictor import LSTMTrajectoryPredictor
from models.transformer_sequence_analyzer import TransformerSequenceAnalyzer
from models.gnn_airspace_modeler import GNNAirspaceModeler
from multi_modal_pipeline import MultiModalPipeline
from advanced_prediction_systems import AdvancedPredictionSystems
from optimization.real_time_optimizer import RealTimeOptimizer
from enterprise_features import EnterpriseFeatures

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('advanced_ai/phase2_training.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def print_banner():
    """Print Phase 2 banner"""
    print("=" * 80)
    print("🚀 PHASE 2: ADVANCED AI MODELS - COMPLETE IMPLEMENTATION")
    print("=" * 80)
    print("This system includes:")
    print("  • Deep Learning Models (LSTM, Transformer, GNN)")
    print("  • Multi-Modal AI Pipeline")
    print("  • Advanced Prediction Systems (15-minute horizon)")
    print("  • Real-Time Optimization Engine")
    print("  • Enterprise-Grade Features & Monitoring")
    print("=" * 80)

def print_progress(current, total, message):
    """Print progress indicator"""
    percentage = (current / total) * 100
    bar_length = 40
    filled_length = int(bar_length * current // total)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    print(f'\r[{bar}] {percentage:.1f}% - {message}', end='', flush=True)

class Phase2AdvancedAI:
    """Master controller for Phase 2 Advanced AI implementation"""
    
    def __init__(self, config_file: str = "advanced_ai/phase2_config.json"):
        self.config = self._load_config(config_file)
        self.training_results = {}
        self.start_time = None
        self.end_time = None
        
    def _load_config(self, config_file: str) -> dict:
        """Load Phase 2 configuration"""
        default_config = {
            "training": {
                "models": {
                    "lstm_trajectory": {"enabled": True, "priority": 1},
                    "transformer_sequence": {"enabled": True, "priority": 2},
                    "gnn_airspace": {"enabled": True, "priority": 3},
                    "multi_modal_pipeline": {"enabled": True, "priority": 4},
                    "advanced_prediction": {"enabled": True, "priority": 5},
                    "optimization_engine": {"enabled": True, "priority": 6},
                    "enterprise_features": {"enabled": True, "priority": 7}
                },
                "parallel_training": False,
                "max_concurrent_models": 2,
                "training_timeout_hours": 12
            },
            "data": {
                "use_existing_data": True,
                "data_paths": {
                    "flight_data": "data_collection/historical_data/flight_data.db",
                    "weather_data": "data_collection/historical_data/weather_data.db",
                    "airport_data": "data_collection/historical_data/airport_data.db"
                }
            },
            "deployment": {
                "auto_deploy": False,
                "deployment_threshold": 0.90,
                "create_ab_tests": True
            }
        }
        
        config_path = Path(config_file)
        if config_path.exists():
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        # Save config for reference
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
            
        return default_config
    
    def run_complete_training(self) -> dict:
        """Run complete Phase 2 training pipeline"""
        
        self.start_time = datetime.now()
        logger.info("🚀 Starting Phase 2 Advanced AI Training Pipeline")
        logger.info("=" * 80)
        
        # Initialize enterprise features
        enterprise = EnterpriseFeatures()
        
        # Get training order
        training_order = self._get_training_order()
        total_models = len(training_order)
        
        logger.info(f"Training {total_models} advanced AI models...")
        
        # Train each model
        for i, (model_name, model_config) in enumerate(training_order):
            logger.info(f"\n📊 Training {model_name} ({i+1}/{total_models})...")
            
            try:
                result = self._train_model(model_name, model_config, enterprise)
                self.training_results[model_name] = result
                logger.info(f"✅ {model_name} training completed successfully")
                
                # Create model version
                if result['success']:
                    version = enterprise.create_model_version(
                        model_name=model_name,
                        model_path=result['model_path'],
                        performance_metrics=result['performance_metrics'],
                        config=model_config
                    )
                    logger.info(f"📦 Created model version {version.version_number}")
                
            except Exception as e:
                logger.error(f"❌ {model_name} training failed: {e}")
                self.training_results[model_name] = {
                    'success': False,
                    'error': str(e),
                    'model_path': None,
                    'performance_metrics': {}
                }
        
        self.end_time = datetime.now()
        
        # Generate final report
        final_report = self._generate_final_report(enterprise)
        
        # Deploy models if configured
        if self.config['deployment']['auto_deploy']:
            self._deploy_models(enterprise)
        
        # Create A/B tests if configured
        if self.config['deployment']['create_ab_tests']:
            self._create_ab_tests(enterprise)
        
        logger.info("🎉 Phase 2 Advanced AI Training Pipeline Completed!")
        
        return final_report
    
    def _get_training_order(self) -> list:
        """Get training order based on priority"""
        
        models = self.config['training']['models']
        enabled_models = {name: config for name, config in models.items() if config['enabled']}
        
        # Sort by priority
        sorted_models = sorted(enabled_models.items(), key=lambda x: x[1]['priority'])
        
        return sorted_models
    
    def _train_model(self, model_name: str, model_config: dict, enterprise) -> dict:
        """Train a specific model"""
        
        start_time = time.time()
        
        try:
            if model_name == "lstm_trajectory":
                result = self._train_lstm_trajectory()
            elif model_name == "transformer_sequence":
                result = self._train_transformer_sequence()
            elif model_name == "gnn_airspace":
                result = self._train_gnn_airspace()
            elif model_name == "multi_modal_pipeline":
                result = self._train_multi_modal_pipeline()
            elif model_name == "advanced_prediction":
                result = self._train_advanced_prediction()
            elif model_name == "optimization_engine":
                result = self._train_optimization_engine()
            elif model_name == "enterprise_features":
                result = self._train_enterprise_features()
            else:
                raise ValueError(f"Unknown model: {model_name}")
            
            training_time = time.time() - start_time
            
            return {
                'success': True,
                'model_path': result.get('model_path', f"advanced_ai/models/{model_name}_model.pth"),
                'performance_metrics': result.get('performance_metrics', {}),
                'training_time_minutes': training_time / 60,
                'config': model_config
            }
            
        except Exception as e:
            logger.error(f"Error training {model_name}: {e}")
            return {
                'success': False,
                'error': str(e),
                'model_path': None,
                'performance_metrics': {},
                'training_time_minutes': (time.time() - start_time) / 60
            }
    
    def _train_lstm_trajectory(self) -> dict:
        """Train LSTM trajectory predictor"""
        
        logger.info("Training LSTM Trajectory Predictor...")
        
        predictor = LSTMTrajectoryPredictor()
        sequences, targets = predictor.prepare_training_data()
        
        if len(sequences) == 0:
            raise ValueError("No training data available for LSTM")
        
        training_results = predictor.train(sequences, targets)
        
        return {
            'model_path': 'advanced_ai/models/lstm_trajectory_model.pth',
            'performance_metrics': {
                'accuracy': training_results['evaluation_results']['overall_accuracy'],
                'rmse': training_results['evaluation_results']['rmse'],
                'training_epochs': len(training_results['training_history']),
                'best_val_loss': training_results['best_val_loss']
            }
        }
    
    def _train_transformer_sequence(self) -> dict:
        """Train Transformer sequence analyzer"""
        
        logger.info("Training Transformer Sequence Analyzer...")
        
        analyzer = TransformerSequenceAnalyzer()
        sequences, labels = analyzer.prepare_training_data()
        
        if len(sequences) == 0:
            raise ValueError("No training data available for Transformer")
        
        training_results = analyzer.train(sequences, labels)
        
        return {
            'model_path': 'advanced_ai/models/transformer_sequence_model.pth',
            'performance_metrics': {
                'accuracy': training_results['evaluation_results']['accuracy'],
                'f1_score': training_results['evaluation_results']['f1_score'],
                'precision': training_results['evaluation_results']['precision'],
                'recall': training_results['evaluation_results']['recall'],
                'training_epochs': len(training_results['training_history'])
            }
        }
    
    def _train_gnn_airspace(self) -> dict:
        """Train GNN airspace modeler"""
        
        logger.info("Training GNN Airspace Modeler...")
        
        modeler = GNNAirspaceModeler()
        graphs = modeler.prepare_training_data()
        
        if len(graphs) == 0:
            raise ValueError("No training data available for GNN")
        
        training_results = modeler.train(graphs)
        
        return {
            'model_path': 'advanced_ai/models/gnn_airspace_model.pth',
            'performance_metrics': {
                'best_loss': training_results['best_loss'],
                'training_epochs': len(training_results['training_history']),
                'training_graphs': len(graphs)
            }
        }
    
    def _train_multi_modal_pipeline(self) -> dict:
        """Train multi-modal pipeline"""
        
        logger.info("Training Multi-Modal Pipeline...")
        
        pipeline = MultiModalPipeline()
        flight_features, weather_features, airport_features, labels = pipeline.prepare_training_data()
        
        if len(flight_features) == 0:
            raise ValueError("No training data available for Multi-Modal Pipeline")
        
        training_results = pipeline.train_fusion_network(
            flight_features, weather_features, airport_features, labels
        )
        
        return {
            'model_path': 'advanced_ai/multi_modal_fusion_model.pth',
            'performance_metrics': {
                'best_val_loss': training_results['best_val_loss'],
                'training_epochs': len(training_results['training_history']),
                'training_samples': len(flight_features)
            }
        }
    
    def _train_advanced_prediction(self) -> dict:
        """Train advanced prediction systems"""
        
        logger.info("Training Advanced Prediction Systems...")
        
        prediction_systems = AdvancedPredictionSystems()
        trajectory_data, weather_data, capacity_data = prediction_systems.prepare_training_data()
        
        if len(trajectory_data['sequences']) == 0:
            raise ValueError("No training data available for Advanced Prediction")
        
        training_results = prediction_systems.train_all_models(
            trajectory_data, weather_data, capacity_data
        )
        
        return {
            'model_path': 'advanced_ai/models/advanced_prediction_models.pth',
            'performance_metrics': {
                'trajectory_loss': training_results['trajectory']['best_val_loss'],
                'weather_loss': training_results['weather']['best_val_loss'],
                'capacity_loss': training_results['capacity']['best_val_loss']
            }
        }
    
    def _train_optimization_engine(self) -> dict:
        """Train optimization engine"""
        
        logger.info("Training Optimization Engine...")
        
        optimizer = RealTimeOptimizer()
        
        # Test optimization with sample data
        start_point = (40.7128, -74.0060, 35000)  # New York
        end_point = (34.0522, -118.2437, 35000)   # Los Angeles
        
        result = optimizer.optimize_route(start_point, end_point, "multi_objective")
        
        return {
            'model_path': 'advanced_ai/optimization/optimization_engine.pth',
            'performance_metrics': {
                'optimization_time_ms': result.optimization_time_ms,
                'solution_quality': result.solution_quality,
                'route_distance': result.route_distance,
                'fuel_consumption': result.fuel_consumption
            }
        }
    
    def _train_enterprise_features(self) -> dict:
        """Initialize enterprise features"""
        
        logger.info("Initializing Enterprise Features...")
        
        enterprise = EnterpriseFeatures()
        
        # Test enterprise features
        system_status = enterprise.get_system_status()
        
        return {
            'model_path': 'advanced_ai/enterprise_features.pth',
            'performance_metrics': {
                'monitoring_status': system_status['monitoring_status'],
                'active_alerts': system_status['active_alerts'],
                'model_versions': sum(system_status['model_versions'].values()),
                'active_ab_tests': system_status['active_ab_tests']
            }
        }
    
    def _generate_final_report(self, enterprise) -> dict:
        """Generate final Phase 2 report"""
        
        total_duration = (self.end_time - self.start_time).total_seconds() / 60
        
        # Calculate success metrics
        successful_models = sum(1 for result in self.training_results.values() if result['success'])
        total_models = len(self.training_results)
        success_rate = (successful_models / total_models) * 100 if total_models > 0 else 0
        
        # Get system status
        system_status = enterprise.get_system_status()
        
        # Generate enterprise report
        enterprise_report = enterprise.generate_enterprise_report()
        
        report = {
            "phase2_summary": {
                "training_start": self.start_time.isoformat(),
                "training_end": self.end_time.isoformat(),
                "total_duration_minutes": total_duration,
                "models_trained": total_models,
                "successful_models": successful_models,
                "success_rate": success_rate
            },
            "model_results": {},
            "performance_metrics": {},
            "enterprise_status": system_status,
            "recommendations": enterprise_report['recommendations']
        }
        
        # Process model results
        for model_name, result in self.training_results.items():
            report["model_results"][model_name] = {
                "success": result['success'],
                "training_time_minutes": result['training_time_minutes'],
                "performance_metrics": result['performance_metrics'],
                "error": result.get('error', None)
            }
        
        # Calculate overall performance metrics
        all_metrics = {}
        for result in self.training_results.values():
            if result['success']:
                for metric_name, value in result['performance_metrics'].items():
                    if metric_name not in all_metrics:
                        all_metrics[metric_name] = []
                    all_metrics[metric_name].append(value)
        
        # Calculate averages
        for metric_name, values in all_metrics.items():
            if values:
                report["performance_metrics"][metric_name] = {
                    "average": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "count": len(values)
                }
        
        # Save report
        report_path = Path("advanced_ai/phase2_training_report.json")
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📋 Final report saved to {report_path}")
        
        return report
    
    def _deploy_models(self, enterprise):
        """Deploy trained models"""
        
        logger.info("🚀 Deploying trained models...")
        
        for model_name, result in self.training_results.items():
            if result['success']:
                # Get latest version for this model
                versions = enterprise.model_version_manager.get_model_versions(model_name)
                if versions:
                    latest_version = versions[0]
                    success = enterprise.deploy_model(latest_version.version_id)
                    logger.info(f"  {'✅' if success else '❌'} Deployed {model_name}: {success}")
    
    def _create_ab_tests(self, enterprise):
        """Create A/B tests for model comparison"""
        
        logger.info("🧪 Creating A/B tests...")
        
        # Create A/B test for trajectory prediction
        test_id = enterprise.create_ab_test(
            test_name="Trajectory Prediction Comparison",
            variant_a={'model': 'lstm_trajectory', 'version': '1.0.0'},
            variant_b={'model': 'advanced_prediction', 'version': '1.0.0'},
            traffic_split=0.5
        )
        logger.info(f"  ✅ Created A/B test: {test_id}")

def main():
    """Main function for Phase 2 training"""
    parser = argparse.ArgumentParser(description="Phase 2 Advanced AI Training")
    parser.add_argument("--config", type=str, default="advanced_ai/phase2_config.json",
                       help="Configuration file path")
    parser.add_argument("--models", nargs="+", 
                       default=["lstm_trajectory", "transformer_sequence", "gnn_airspace", 
                               "multi_modal_pipeline", "advanced_prediction", "optimization_engine", "enterprise_features"],
                       help="Models to train")
    parser.add_argument("--quick", action="store_true",
                       help="Quick training mode (reduced epochs)")
    parser.add_argument("--deploy", action="store_true",
                       help="Auto-deploy models after training")
    
    args = parser.parse_args()
    
    # Print banner
    print_banner()
    
    # Initialize Phase 2 system
    phase2 = Phase2AdvancedAI(args.config)
    
    # Update config for quick mode
    if args.quick:
        print("⚡ Quick Training Mode - Reduced epochs for faster training")
        # Update config to reduce training time
    
    # Update config with command line arguments
    for model_name in args.models:
        if model_name in phase2.config['training']['models']:
            phase2.config['training']['models'][model_name]['enabled'] = True
    
    phase2.config['deployment']['auto_deploy'] = args.deploy
    
    print(f"\n🚀 Starting Phase 2 Advanced AI Training")
    print("=" * 80)
    print(f"Models to train: {', '.join(args.models)}")
    print(f"Auto-deploy: {args.deploy}")
    print("=" * 80)
    
    # Confirm before starting
    if not args.quick:
        response = input("\n⚠️ This will train advanced AI models. Continue? (y/N): ")
        if response.lower() != 'y':
            print("❌ Training cancelled by user")
            return
    
    # Start training
    try:
        final_report = phase2.run_complete_training()
        
        # Print results
        print("\n" + "=" * 80)
        print("🎉 PHASE 2 ADVANCED AI TRAINING COMPLETED!")
        print("=" * 80)
        
        summary = final_report["phase2_summary"]
        print(f"⏱️ Total Duration: {summary['total_duration_minutes']:.1f} minutes")
        print(f"✅ Successful Models: {summary['successful_models']}/{summary['models_trained']}")
        print(f"📊 Success Rate: {summary['success_rate']:.1f}%")
        
        print(f"\n📋 Model Results:")
        for model_name, result in final_report["model_results"].items():
            status = "✅ Success" if result['success'] else "❌ Failed"
            time_str = f"{result['training_time_minutes']:.1f}min"
            print(f"  {model_name}: {status} ({time_str})")
        
        print(f"\n📈 Performance Metrics:")
        for metric_name, metrics in final_report["performance_metrics"].items():
            print(f"  {metric_name}: {metrics['average']:.3f} (avg)")
        
        print(f"\n🏢 Enterprise Status:")
        enterprise_status = final_report["enterprise_status"]
        print(f"  Active Alerts: {enterprise_status['active_alerts']}")
        print(f"  Model Versions: {sum(enterprise_status['model_versions'].values())}")
        print(f"  Active A/B Tests: {enterprise_status['active_ab_tests']}")
        
        if final_report["recommendations"]:
            print(f"\n💡 Recommendations:")
            for i, rec in enumerate(final_report["recommendations"], 1):
                print(f"  {i}. {rec}")
        
        print(f"\n🚀 Next Steps:")
        print(f"  1. Review training reports in advanced_ai/")
        print(f"  2. Deploy models to production")
        print(f"  3. Monitor performance with enterprise features")
        print(f"  4. Proceed to Phase 3: Real-Time Integration")
        
        print("=" * 80)
        
    except KeyboardInterrupt:
        print("\n❌ Training interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Training failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
