"""
MLOps Monitoring & Drift Detection Module
Implements production monitoring for credit risk models
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import yaml
import joblib
from datetime import datetime
from loguru import logger


class ModelMonitor:
    """
    Production model monitoring system.
    
    Implements:
    - Population Stability Index (PSI) for data drift
    - Model performance monitoring
    - Prediction distribution tracking
    - Retraining triggers
    - Alert system
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize model monitor with configuration."""
        config_file = Path(config_path)
        if not config_file.exists():
            root_config = Path(__file__).resolve().parents[2] / "config.yaml"
            if root_config.exists():
                config_file = root_config

        with open(config_file, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.monitoring_config = self.config['monitoring']
        self.psi_threshold = self.monitoring_config['psi_threshold']
        self.psi_bins = self.monitoring_config['psi_bins']
        
        # Storage for monitoring data
        self.baseline_stats = {}
        self.production_stats = []
        self.alerts = []
        
        logger.info("ModelMonitor initialized")
        logger.info(f"PSI threshold: {self.psi_threshold}")
    
    def set_baseline(self, df: pd.DataFrame, feature_cols: List[str],
                    target_col: Optional[str] = None) -> None:
        """
        Set baseline statistics from training/validation data.
        
        Args:
            df: Baseline dataset
            feature_cols: List of feature columns
            target_col: Optional target column for performance baseline
        """
        logger.info("Setting baseline statistics...")
        
        self.baseline_stats = {
            'n_samples': len(df),
            'timestamp': datetime.now().isoformat(),
            'features': {}
        }
        
        # Compute feature distributions
        for col in feature_cols:
            if col not in df.columns:
                continue
            
            feature_data = df[col].dropna()
            
            if pd.api.types.is_numeric_dtype(feature_data):
                # Numeric features: compute quantile bins
                bins = np.percentile(
                    feature_data, 
                    np.linspace(0, 100, self.psi_bins + 1)
                )
                # Ensure unique bins
                bins = np.unique(bins)
                
                # Compute baseline distribution
                hist, bin_edges = np.histogram(feature_data, bins=bins)
                distribution = hist / hist.sum()
                
                self.baseline_stats['features'][col] = {
                    'type': 'numeric',
                    'bins': bin_edges.tolist(),
                    'distribution': distribution.tolist(),
                    'mean': float(feature_data.mean()),
                    'std': float(feature_data.std()),
                    'min': float(feature_data.min()),
                    'max': float(feature_data.max())
                }
            else:
                # Categorical features: compute value counts
                value_counts = feature_data.value_counts(normalize=True)
                
                self.baseline_stats['features'][col] = {
                    'type': 'categorical',
                    'distribution': value_counts.to_dict(),
                    'n_unique': int(feature_data.nunique())
                }
        
        # Set target baseline if provided
        if target_col and target_col in df.columns:
            self.baseline_stats['target'] = {
                'mean': float(df[target_col].mean()),
                'distribution': df[target_col].value_counts(normalize=True).to_dict()
            }
        
        logger.info(f"Baseline set with {len(feature_cols)} features from {len(df)} samples")
    
    def compute_psi(self, baseline_dist: np.ndarray, current_dist: np.ndarray) -> float:
        """
        Compute Population Stability Index (PSI).
        
        PSI measures drift between two distributions:
        - PSI < 0.1: No significant change
        - 0.1 <= PSI < 0.2: Moderate change (monitor)
        - PSI >= 0.2: Significant change (retrain)
        
        Args:
            baseline_dist: Baseline distribution
            current_dist: Current distribution
            
        Returns:
            PSI value
        """
        # Avoid division by zero and log(0)
        baseline_dist = np.where(baseline_dist == 0, 0.0001, baseline_dist)
        current_dist = np.where(current_dist == 0, 0.0001, current_dist)
        
        psi = np.sum((current_dist - baseline_dist) * np.log(current_dist / baseline_dist))
        
        return psi
    
    def detect_feature_drift(self, df: pd.DataFrame, feature_cols: List[str]) -> Dict[str, Any]:
        """
        Detect feature drift using PSI.
        
        Args:
            df: Current production data
            feature_cols: List of features to check
            
        Returns:
            Dictionary with drift results
        """
        if not self.baseline_stats or 'features' not in self.baseline_stats:
            logger.error("Baseline not set. Call set_baseline first.")
            return {}
        
        logger.info(f"Detecting drift for {len(feature_cols)} features...")
        
        drift_results = {
            'timestamp': datetime.now().isoformat(),
            'n_samples': len(df),
            'features': {},
            'summary': {
                'no_drift': 0,
                'moderate_drift': 0,
                'high_drift': 0
            }
        }
        
        for col in feature_cols:
            if col not in df.columns or col not in self.baseline_stats['features']:
                continue
            
            baseline_info = self.baseline_stats['features'][col]
            current_data = df[col].dropna()
            
            if len(current_data) == 0:
                continue
            
            if baseline_info['type'] == 'numeric':
                # Use baseline bins
                bins = np.array(baseline_info['bins'])
                baseline_dist = np.array(baseline_info['distribution'])
                
                # Compute current distribution
                hist, _ = np.histogram(current_data, bins=bins)
                current_dist = hist / hist.sum() if hist.sum() > 0 else hist
                
                # Ensure same length
                if len(current_dist) != len(baseline_dist):
                    logger.warning(f"Distribution length mismatch for {col}")
                    continue
                
                # Compute PSI
                psi = self.compute_psi(baseline_dist, current_dist)
                
                # Determine drift level
                if psi < 0.1:
                    drift_level = 'no_drift'
                elif psi < 0.2:
                    drift_level = 'moderate_drift'
                else:
                    drift_level = 'high_drift'
                
                drift_results['features'][col] = {
                    'psi': float(psi),
                    'drift_level': drift_level,
                    'mean_shift': float(current_data.mean() - baseline_info['mean']),
                    'std_shift': float(current_data.std() - baseline_info['std'])
                }
                
                drift_results['summary'][drift_level] += 1
            
            elif baseline_info['type'] == 'categorical':
                # Compare categorical distributions
                baseline_dist = baseline_info['distribution']
                current_dist = current_data.value_counts(normalize=True).to_dict()
                
                # Align distributions
                all_categories = set(baseline_dist.keys()) | set(current_dist.keys())
                
                baseline_arr = np.array([baseline_dist.get(cat, 0.0001) for cat in all_categories])
                current_arr = np.array([current_dist.get(cat, 0.0001) for cat in all_categories])
                
                # Normalize
                baseline_arr = baseline_arr / baseline_arr.sum()
                current_arr = current_arr / current_arr.sum()
                
                # Compute PSI
                psi = self.compute_psi(baseline_arr, current_arr)
                
                drift_level = 'no_drift' if psi < 0.1 else ('moderate_drift' if psi < 0.2 else 'high_drift')
                
                drift_results['features'][col] = {
                    'psi': float(psi),
                    'drift_level': drift_level,
                    'n_unique_baseline': baseline_info['n_unique'],
                    'n_unique_current': int(current_data.nunique())
                }
                
                drift_results['summary'][drift_level] += 1
        
        # Log summary
        logger.info("\nDrift Detection Summary:")
        logger.info(f"  No drift: {drift_results['summary']['no_drift']}")
        logger.info(f"  Moderate drift: {drift_results['summary']['moderate_drift']}")
        logger.info(f"  High drift: {drift_results['summary']['high_drift']}")
        
        # Check if retraining is needed
        if drift_results['summary']['high_drift'] > 0:
            self._create_alert('HIGH_DRIFT', 
                             f"{drift_results['summary']['high_drift']} features show high drift (PSI >= 0.2)")
        
        return drift_results
    
    def monitor_predictions(self, predictions: np.ndarray, 
                          description: str = "production") -> Dict[str, Any]:
        """
        Monitor prediction distributions.
        
        Args:
            predictions: Array of model predictions
            description: Description of prediction batch
            
        Returns:
            Dictionary with prediction statistics
        """
        stats = {
            'timestamp': datetime.now().isoformat(),
            'description': description,
            'n_predictions': len(predictions),
            'mean': float(np.mean(predictions)),
            'median': float(np.median(predictions)),
            'std': float(np.std(predictions)),
            'min': float(np.min(predictions)),
            'max': float(np.max(predictions)),
            'percentiles': {
                'p5': float(np.percentile(predictions, 5)),
                'p25': float(np.percentile(predictions, 25)),
                'p75': float(np.percentile(predictions, 75)),
                'p95': float(np.percentile(predictions, 95))
            }
        }
        
        self.production_stats.append(stats)
        
        # Check for anomalies
        if 'target' in self.baseline_stats:
            baseline_mean = self.baseline_stats['target']['mean']
            if abs(stats['mean'] - baseline_mean) > 0.05:  # 5% deviation
                self._create_alert('PREDICTION_DRIFT',
                                 f"Mean prediction shifted from {baseline_mean:.3f} to {stats['mean']:.3f}")
        
        return stats
    
    def check_retraining_trigger(self, drift_results: Dict[str, Any],
                                performance_metrics: Optional[Dict] = None) -> Tuple[bool, List[str]]:
        """
        Check if model retraining should be triggered.
        
        Args:
            drift_results: Results from drift detection
            performance_metrics: Optional performance metrics from production
            
        Returns:
            Tuple of (should_retrain, reasons)
        """
        reasons = []
        
        # Check drift-based trigger
        if self.monitoring_config.get('retrain_on_psi', True):
            retrain_psi_threshold = self.monitoring_config.get('retrain_psi_threshold', 0.15)
            
            high_drift_features = [
                feat for feat, info in drift_results.get('features', {}).items()
                if info.get('psi', 0) > retrain_psi_threshold
            ]
            
            if high_drift_features:
                reasons.append(f"High PSI detected in {len(high_drift_features)} features")
        
        # Check performance-based trigger
        if performance_metrics and self.monitoring_config.get('retrain_on_performance_drop', True):
            drop_threshold = self.monitoring_config.get('performance_drop_threshold', 0.05)
            
            if 'auc' in performance_metrics and 'auc' in self.baseline_stats.get('performance', {}):
                baseline_auc = self.baseline_stats['performance']['auc']
                current_auc = performance_metrics['auc']
                
                if baseline_auc - current_auc > drop_threshold:
                    reasons.append(f"AUC dropped from {baseline_auc:.4f} to {current_auc:.4f}")
        
        should_retrain = len(reasons) > 0
        
        if should_retrain:
            logger.warning("RETRAINING RECOMMENDED")
            for reason in reasons:
                logger.warning(f"  - {reason}")
        
        return should_retrain, reasons
    
    def _create_alert(self, alert_type: str, message: str) -> None:
        """Create monitoring alert."""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'type': alert_type,
            'message': message
        }
        
        self.alerts.append(alert)
        logger.warning(f"ALERT [{alert_type}]: {message}")
    
    def get_alerts(self, last_n: Optional[int] = None) -> List[Dict]:
        """
        Get monitoring alerts.
        
        Args:
            last_n: Number of recent alerts to return (None for all)
            
        Returns:
            List of alert dictionaries
        """
        if last_n:
            return self.alerts[-last_n:]
        return self.alerts
    
    def generate_monitoring_report(self, save_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate comprehensive monitoring report.
        
        Args:
            save_path: Path to save report
            
        Returns:
            Dictionary with monitoring report
        """
        report = {
            'baseline': self.baseline_stats,
            'production_batches': len(self.production_stats),
            'alerts': self.alerts,
            'summary': {
                'total_alerts': len(self.alerts),
                'alert_types': {}
            }
        }
        
        # Aggregate alert types
        for alert in self.alerts:
            alert_type = alert['type']
            report['summary']['alert_types'][alert_type] = \
                report['summary']['alert_types'].get(alert_type, 0) + 1
        
        if save_path:
            joblib.dump(report, save_path)
            logger.info(f"Monitoring report saved to {save_path}")
        
        return report
    
    def save_monitoring_state(self, save_dir: str = "models") -> None:
        """Save monitoring state and statistics."""
        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)
        
        state = {
            'baseline_stats': self.baseline_stats,
            'production_stats': self.production_stats,
            'alerts': self.alerts
        }
        
        joblib.dump(state, save_path / "monitoring_state.pkl")
        logger.info(f"Monitoring state saved to {save_path}")
    
    def load_monitoring_state(self, load_dir: str = "models") -> None:
        """Load monitoring state and statistics."""
        load_path = Path(load_dir) / "monitoring_state.pkl"
        
        if not load_path.exists():
            logger.warning(f"Monitoring state not found at {load_path}")
            return
        
        state = joblib.load(load_path)
        
        self.baseline_stats = state.get('baseline_stats', {})
        self.production_stats = state.get('production_stats', [])
        self.alerts = state.get('alerts', [])
        
        logger.info(f"Monitoring state loaded from {load_path}")


if __name__ == "__main__":
    logger.info("MLOps Monitoring module loaded successfully")
