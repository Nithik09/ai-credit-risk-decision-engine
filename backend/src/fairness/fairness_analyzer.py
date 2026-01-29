"""
Fairness & Bias Detection Module for Credit Risk Models
Ensures compliance with ECOA, FCRA, and fairness regulations
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import yaml
from loguru import logger
import matplotlib.pyplot as plt
import seaborn as sns


class FairnessAnalyzer:
    """
    Analyzes model fairness across demographic and proxy groups.
    
    Implements:
    - Disparate Impact analysis
    - Equal Opportunity metrics
    - Fairness metrics (TPR, FPR, precision parity)
    - Bias detection across protected attributes
    
    Note: Uses proxy features since protected attributes (race, religion) 
    are typically not available in credit data.
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize fairness analyzer with configuration."""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.proxy_features = self.config['fairness']['proxy_features']
        self.metrics = self.config['fairness']['metrics']
        self.di_threshold = self.config['fairness']['disparate_impact_threshold']
        
        self.fairness_results = {}
        
        logger.info("FairnessAnalyzer initialized")
    
    def compute_group_metrics(self, df: pd.DataFrame, y_true_col: str,
                             y_pred_col: str, y_score_col: str,
                             group_col: str, threshold: float = 0.5) -> pd.DataFrame:
        """
        Compute fairness metrics for each group in a protected/proxy attribute.
        
        Args:
            df: DataFrame with predictions and actuals
            y_true_col: Column name for true labels
            y_pred_col: Column name for predicted decisions (0/1)
            y_score_col: Column name for predicted scores/probabilities
            group_col: Column name for group attribute
            threshold: Decision threshold
            
        Returns:
            DataFrame with metrics per group
        """
        logger.info(f"Computing fairness metrics for {group_col}...")
        
        metrics_list = []
        
        for group_value in df[group_col].unique():
            if pd.isna(group_value):
                continue
            
            # Filter to group
            group_df = df[df[group_col] == group_value].copy()
            
            if len(group_df) == 0:
                continue
            
            # Get predictions and actuals
            y_true = group_df[y_true_col]
            y_pred = (group_df[y_score_col] >= threshold).astype(int)
            
            # Basic counts
            n_samples = len(group_df)
            n_positive = y_true.sum()
            n_negative = len(y_true) - n_positive
            
            # Predictions
            n_pred_positive = y_pred.sum()
            n_pred_negative = len(y_pred) - n_pred_positive
            
            # Confusion matrix components
            tp = ((y_true == 1) & (y_pred == 1)).sum()
            tn = ((y_true == 0) & (y_pred == 0)).sum()
            fp = ((y_true == 0) & (y_pred == 1)).sum()
            fn = ((y_true == 1) & (y_pred == 0)).sum()
            
            # Metrics
            metrics = {
                'group': group_value,
                'n_samples': n_samples,
                'n_positive': n_positive,
                'n_negative': n_negative,
                'base_rate': n_positive / n_samples if n_samples > 0 else 0,
                
                # Approval metrics (for credit: pred=0 is approval, pred=1 is rejection)
                'approval_rate': 1 - (n_pred_positive / n_samples) if n_samples > 0 else 0,
                'rejection_rate': n_pred_positive / n_samples if n_samples > 0 else 0,
                
                # Performance metrics
                'true_positive_rate': tp / n_positive if n_positive > 0 else 0,  # Recall, Sensitivity
                'false_positive_rate': fp / n_negative if n_negative > 0 else 0,
                'true_negative_rate': tn / n_negative if n_negative > 0 else 0,  # Specificity
                'false_negative_rate': fn / n_positive if n_positive > 0 else 0,
                
                'precision': tp / n_pred_positive if n_pred_positive > 0 else 0,
                'accuracy': (tp + tn) / n_samples if n_samples > 0 else 0,
                
                # F1 score
                'f1_score': 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) > 0 else 0,
                
                # Average score
                'mean_score': group_df[y_score_col].mean()
            }
            
            metrics_list.append(metrics)
        
        metrics_df = pd.DataFrame(metrics_list)
        
        logger.info(f"Computed metrics for {len(metrics_df)} groups")
        return metrics_df
    
    def compute_disparate_impact(self, metrics_df: pd.DataFrame,
                                metric: str = 'approval_rate') -> Dict[str, float]:
        """
        Compute disparate impact ratios.
        
        Disparate impact is the ratio of the metric for the disadvantaged group
        to the metric for the advantaged group. 
        
        The "80% rule" states that DI should be >= 0.8.
        
        Args:
            metrics_df: DataFrame with group metrics
            metric: Metric to analyze (e.g., 'approval_rate')
            
        Returns:
            Dictionary with disparate impact analysis
        """
        if len(metrics_df) < 2:
            logger.warning("Need at least 2 groups for disparate impact analysis")
            return {}
        
        # Find group with highest and lowest metric
        max_group = metrics_df.loc[metrics_df[metric].idxmax()]
        min_group = metrics_df.loc[metrics_df[metric].idxmin()]
        
        # Disparate impact ratio
        di_ratio = min_group[metric] / max_group[metric] if max_group[metric] > 0 else 0
        
        result = {
            'metric': metric,
            'advantaged_group': max_group['group'],
            'advantaged_value': max_group[metric],
            'disadvantaged_group': min_group['group'],
            'disadvantaged_value': min_group[metric],
            'disparate_impact_ratio': di_ratio,
            'passes_80_rule': di_ratio >= self.di_threshold,
            'difference': max_group[metric] - min_group[metric]
        }
        
        logger.info(f"Disparate Impact ({metric}): {di_ratio:.3f} "
                   f"({'PASS' if result['passes_80_rule'] else 'FAIL'})")
        
        return result
    
    def analyze_fairness(self, df: pd.DataFrame, y_true_col: str = 'TARGET',
                        y_score_col: str = 'predicted_proba',
                        threshold: float = 0.15) -> Dict[str, Any]:
        """
        Perform comprehensive fairness analysis across all proxy features.
        
        Args:
            df: DataFrame with predictions, actuals, and proxy features
            y_true_col: True label column
            y_score_col: Predicted score/probability column
            threshold: Decision threshold (reject if score > threshold)
            
        Returns:
            Dictionary with fairness analysis results
        """
        logger.info("Performing comprehensive fairness analysis...")
        
        # Create binary decision
        df = df.copy()
        df['predicted_decision'] = (df[y_score_col] >= threshold).astype(int)
        
        results = {}
        
        for proxy_feature in self.proxy_features:
            if proxy_feature not in df.columns:
                logger.warning(f"Proxy feature {proxy_feature} not found in data")
                continue
            
            logger.info(f"\n{'='*60}")
            logger.info(f"Analyzing fairness for: {proxy_feature}")
            logger.info(f"{'='*60}")
            
            # Compute group metrics
            group_metrics = self.compute_group_metrics(
                df, y_true_col, 'predicted_decision', y_score_col, proxy_feature, threshold
            )
            
            # Compute disparate impact for each metric
            di_results = {}
            for metric in self.metrics:
                if metric in group_metrics.columns:
                    di_results[metric] = self.compute_disparate_impact(group_metrics, metric)
            
            # Store results
            results[proxy_feature] = {
                'group_metrics': group_metrics,
                'disparate_impact': di_results
            }
            
            # Log summary
            self._log_fairness_summary(proxy_feature, group_metrics, di_results)
        
        self.fairness_results = results
        return results
    
    def _log_fairness_summary(self, feature: str, group_metrics: pd.DataFrame,
                             di_results: Dict) -> None:
        """Log summary of fairness analysis."""
        logger.info(f"\nGroup Metrics for {feature}:")
        logger.info(group_metrics[['group', 'n_samples', 'approval_rate', 
                                   'true_positive_rate', 'false_positive_rate']].to_string())
        
        logger.info(f"\nDisparate Impact Summary:")
        for metric, di in di_results.items():
            if di:
                status = "✓ PASS" if di['passes_80_rule'] else "✗ FAIL"
                logger.info(f"  {metric}: {di['disparate_impact_ratio']:.3f} {status}")
    
    def detect_bias(self, threshold: float = None) -> Dict[str, List[str]]:
        """
        Detect potential biases based on fairness thresholds.
        
        Args:
            threshold: Disparate impact threshold (default from config)
            
        Returns:
            Dictionary with bias warnings
        """
        if threshold is None:
            threshold = self.di_threshold
        
        if not self.fairness_results:
            logger.warning("No fairness results available. Run analyze_fairness first.")
            return {}
        
        biases = {
            'high_concern': [],
            'moderate_concern': [],
            'acceptable': []
        }
        
        for feature, results in self.fairness_results.items():
            di_results = results['disparate_impact']
            
            for metric, di in di_results.items():
                if not di:
                    continue
                
                ratio = di['disparate_impact_ratio']
                
                if ratio < 0.7:
                    biases['high_concern'].append(
                        f"{feature} - {metric}: DI ratio = {ratio:.3f}"
                    )
                elif ratio < threshold:
                    biases['moderate_concern'].append(
                        f"{feature} - {metric}: DI ratio = {ratio:.3f}"
                    )
                else:
                    biases['acceptable'].append(
                        f"{feature} - {metric}: DI ratio = {ratio:.3f}"
                    )
        
        # Log summary
        logger.info("\n" + "="*60)
        logger.info("BIAS DETECTION SUMMARY")
        logger.info("="*60)
        logger.info(f"High Concern (DI < 0.7): {len(biases['high_concern'])}")
        logger.info(f"Moderate Concern (DI < {threshold}): {len(biases['moderate_concern'])}")
        logger.info(f"Acceptable (DI >= {threshold}): {len(biases['acceptable'])}")
        
        if biases['high_concern']:
            logger.warning("\nHigh Concern Items:")
            for item in biases['high_concern']:
                logger.warning(f"  - {item}")
        
        return biases
    
    def plot_fairness_metrics(self, feature: str, metrics: List[str] = None,
                             save_path: Optional[str] = None) -> None:
        """
        Plot fairness metrics across groups.
        
        Args:
            feature: Proxy feature to plot
            metrics: List of metrics to plot (default: from config)
            save_path: Path to save plot
        """
        if feature not in self.fairness_results:
            logger.error(f"No fairness results for {feature}")
            return
        
        if metrics is None:
            metrics = self.metrics[:4]  # Plot first 4 metrics
        
        group_metrics = self.fairness_results[feature]['group_metrics']
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        axes = axes.flatten()
        
        for idx, metric in enumerate(metrics):
            if metric not in group_metrics.columns:
                continue
            
            ax = axes[idx]
            
            # Bar plot
            groups = group_metrics['group'].astype(str)
            values = group_metrics[metric]
            
            bars = ax.bar(range(len(groups)), values, alpha=0.7)
            
            # Color bars based on disparate impact
            di_result = self.fairness_results[feature]['disparate_impact'].get(metric, {})
            if di_result:
                adv_group = str(di_result['advantaged_group'])
                dis_group = str(di_result['disadvantaged_group'])
                
                for i, group in enumerate(groups):
                    if group == adv_group:
                        bars[i].set_color('green')
                    elif group == dis_group:
                        bars[i].set_color('red')
            
            ax.set_xticks(range(len(groups)))
            ax.set_xticklabels(groups, rotation=45)
            ax.set_ylabel(metric.replace('_', ' ').title())
            ax.set_title(f"{metric.replace('_', ' ').title()} by {feature}")
            ax.grid(alpha=0.3)
            
            # Add disparate impact ratio as text
            if di_result:
                di_ratio = di_result['disparate_impact_ratio']
                status = "PASS" if di_result['passes_80_rule'] else "FAIL"
                ax.text(0.5, 0.95, f"DI Ratio: {di_ratio:.3f} ({status})",
                       transform=ax.transAxes, ha='center', va='top',
                       bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Fairness plot saved to {save_path}")
        else:
            plt.show()
        
        plt.close()
    
    def generate_fairness_report(self, save_path: Optional[str] = None) -> pd.DataFrame:
        """
        Generate comprehensive fairness report.
        
        Args:
            save_path: Path to save report CSV
            
        Returns:
            DataFrame with fairness report
        """
        if not self.fairness_results:
            logger.warning("No fairness results available")
            return pd.DataFrame()
        
        report_rows = []
        
        for feature, results in self.fairness_results.items():
            di_results = results['disparate_impact']
            
            for metric, di in di_results.items():
                if not di:
                    continue
                
                row = {
                    'proxy_feature': feature,
                    'metric': metric,
                    'advantaged_group': di['advantaged_group'],
                    'advantaged_value': di['advantaged_value'],
                    'disadvantaged_group': di['disadvantaged_group'],
                    'disadvantaged_value': di['disadvantaged_value'],
                    'disparate_impact_ratio': di['disparate_impact_ratio'],
                    'passes_80_rule': di['passes_80_rule'],
                    'absolute_difference': di['difference']
                }
                
                report_rows.append(row)
        
        report_df = pd.DataFrame(report_rows)
        
        if save_path:
            report_df.to_csv(save_path, index=False)
            logger.info(f"Fairness report saved to {save_path}")
        
        return report_df
    
    def get_mitigation_recommendations(self) -> List[str]:
        """
        Get recommendations for mitigating detected biases.
        
        Returns:
            List of mitigation recommendations
        """
        biases = self.detect_bias()
        
        recommendations = []
        
        if biases['high_concern'] or biases['moderate_concern']:
            recommendations.append(
                "1. REWEIGHTING: Adjust training data weights to balance group representation"
            )
            recommendations.append(
                "2. THRESHOLD OPTIMIZATION: Set group-specific thresholds to equalize opportunity"
            )
            recommendations.append(
                "3. FEATURE REVIEW: Remove or reduce weight of potentially discriminatory features"
            )
            recommendations.append(
                "4. FAIRNESS CONSTRAINTS: Add fairness constraints during model training"
            )
            recommendations.append(
                "5. POST-PROCESSING: Apply calibration or rejection option to reduce disparate impact"
            )
            recommendations.append(
                "6. ADDITIONAL DATA: Collect more data from underrepresented groups"
            )
        else:
            recommendations.append("Model shows acceptable fairness metrics across all groups.")
            recommendations.append("Continue monitoring fairness in production.")
        
        return recommendations


if __name__ == "__main__":
    logger.info("Fairness & Bias Detection module loaded successfully")
