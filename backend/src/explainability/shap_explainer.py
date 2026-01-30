"""
SHAP Explainability Module for Credit Risk Models
Provides global and local model interpretations for regulatory compliance
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Any
from pathlib import Path
import yaml
import joblib
from loguru import logger

import shap
import matplotlib.pyplot as plt
import seaborn as sns


class ModelExplainer:
    """
    Provides SHAP-based explanations for credit risk models.
    
    Key capabilities:
    - Global feature importance
    - Local (instance-level) explanations
    - Adverse action reasons (ECOA/FCRA compliant)
    - Summary and dependence plots
    """
    
    def __init__(self, model: Any, X_background: pd.DataFrame, config_path: str = "config.yaml"):
        """
        Initialize explainer with model and background data.
        
        Args:
            model: Trained model
            X_background: Background dataset for SHAP (typically training sample)
            config_path: Path to configuration file
        """
        config_file = Path(config_path)
        if not config_file.exists():
            root_config = Path(__file__).resolve().parents[2] / "config.yaml"
            if root_config.exists():
                config_file = root_config

        with open(config_file, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.model = model
        self.feature_names = X_background.columns.tolist()
        
        # Sample background data for efficiency
        background_size = self.config['explainability']['background_samples']
        if len(X_background) > background_size:
            self.X_background = X_background.sample(n=background_size, random_state=42)
        else:
            self.X_background = X_background
        
        logger.info("Initializing SHAP explainer...")
        self.explainer = self._create_explainer()
        self.shap_values = None
        self.base_value = None
        
        logger.info("ModelExplainer initialized")
    
    def _create_explainer(self) -> shap.Explainer:
        """
        Create appropriate SHAP explainer based on model type.
        
        Returns:
            SHAP Explainer object
        """
        model_type = str(type(self.model)).lower()
        
        # Tree-based models (LightGBM, XGBoost) use TreeExplainer
        if 'lightgbm' in model_type or 'lgbm' in model_type:
            logger.info("Using TreeExplainer for LightGBM")
            return shap.TreeExplainer(self.model)
        elif 'xgb' in model_type:
            logger.info("Using TreeExplainer for XGBoost")
            return shap.TreeExplainer(self.model)
        elif 'calibrated' in model_type:
            # For calibrated classifier, use the base estimator
            logger.info("Using TreeExplainer for calibrated model")
            base_estimator = self.model.calibrated_classifiers_[0].estimator
            return shap.TreeExplainer(base_estimator)
        else:
            # Fallback to KernelExplainer (slower but works for any model)
            logger.warning("Using KernelExplainer (slower)")
            return shap.KernelExplainer(
                self.model.predict_proba,
                self.X_background,
                link="logit"
            )
    
    def compute_shap_values(self, X: pd.DataFrame, sample_size: Optional[int] = None) -> np.ndarray:
        """
        Compute SHAP values for given data.
        
        Args:
            X: Features to explain
            sample_size: If provided, sample this many instances
            
        Returns:
            SHAP values array
        """
        if sample_size is None:
            sample_size = self.config['explainability']['shap_sample_size']
        
        # Sample if dataset is large
        if len(X) > sample_size:
            logger.info(f"Sampling {sample_size} instances for SHAP computation")
            X_sample = X.sample(n=sample_size, random_state=42)
        else:
            X_sample = X
        
        logger.info(f"Computing SHAP values for {len(X_sample)} instances...")
        
        # Compute SHAP values
        shap_values = self.explainer.shap_values(X_sample)
        
        # Handle multi-output (binary classification)
        if isinstance(shap_values, list):
            # Use positive class (default) SHAP values
            shap_values = shap_values[1]
        
        self.shap_values = shap_values
        
        # Get base value (expected value)
        if hasattr(self.explainer, 'expected_value'):
            self.base_value = self.explainer.expected_value
            if isinstance(self.base_value, list):
                self.base_value = self.base_value[1]
        
        logger.info("SHAP values computed")
        return shap_values
    
    def get_global_importance(self, X: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
        """
        Get global feature importance using SHAP values.
        
        Args:
            X: Features
            top_n: Number of top features to return
            
        Returns:
            DataFrame with feature importance
        """
        if self.shap_values is None:
            self.compute_shap_values(X)
        
        # Mean absolute SHAP value for each feature
        importance = np.abs(self.shap_values).mean(axis=0)
        
        importance_df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': importance
        }).sort_values('importance', ascending=False)
        
        logger.info(f"Top {top_n} most important features computed")
        return importance_df.head(top_n)
    
    def explain_instance(self, X: pd.DataFrame, instance_idx: int = 0,
                        num_features: Optional[int] = None) -> Dict[str, Any]:
        """
        Get local explanation for a single instance.
        
        Args:
            X: Features
            instance_idx: Index of instance to explain
            num_features: Number of top features to include
            
        Returns:
            Dictionary with explanation details
        """
        if num_features is None:
            num_features = self.config['explainability']['num_top_features']
        
        # Compute SHAP values if not already done
        if self.shap_values is None or len(self.shap_values) <= instance_idx:
            self.compute_shap_values(X)
        
        instance_shap = self.shap_values[instance_idx]
        instance_features = X.iloc[instance_idx]
        
        # Create feature contributions
        contributions = []
        for feature, shap_val, feat_val in zip(self.feature_names, instance_shap, instance_features):
            contributions.append({
                'feature': feature,
                'value': feat_val,
                'shap_value': shap_val,
                'abs_shap': abs(shap_val)
            })
        
        # Sort by absolute SHAP value
        contributions = sorted(contributions, key=lambda x: x['abs_shap'], reverse=True)
        
        explanation = {
            'base_value': self.base_value,
            'prediction_value': self.base_value + instance_shap.sum() if self.base_value else instance_shap.sum(),
            'top_features': contributions[:num_features]
        }
        
        return explanation
    
    def generate_adverse_action_reasons(self, X: pd.DataFrame, instance_idx: int,
                                       num_reasons: int = 4) -> List[str]:
        """
        Generate adverse action reasons for rejected applicants (ECOA/FCRA compliance).
        
        Per regulation, must provide specific reasons when credit is denied.
        Uses features with highest negative SHAP values (increasing PD).
        
        Args:
            X: Features
            instance_idx: Index of instance
            num_reasons: Number of reasons to generate (typically 4-5)
            
        Returns:
            List of human-readable adverse action reasons
        """
        explanation = self.explain_instance(X, instance_idx, num_features=20)
        
        # Get features that increased default probability (positive SHAP for default class)
        adverse_features = [f for f in explanation['top_features'] if f['shap_value'] > 0]
        
        # Take top N reasons
        adverse_features = adverse_features[:num_reasons]
        
        # Generate human-readable reasons
        reasons = []
        for feat in adverse_features:
            reason = self._feature_to_adverse_reason(feat['feature'], feat['value'], feat['shap_value'])
            reasons.append(reason)
        
        logger.info(f"Generated {len(reasons)} adverse action reasons")
        return reasons
    
    def _feature_to_adverse_reason(self, feature: str, value: Any, shap_value: float) -> str:
        """
        Convert feature name and value to human-readable adverse action reason.
        
        Args:
            feature: Feature name
            value: Feature value
            shap_value: SHAP contribution
            
        Returns:
            Human-readable reason
        """
        # Map technical features to business language
        reason_mapping = {
            'EXT_SOURCE': 'Credit bureau score lower than typical approved applicants',
            'CREDIT_INCOME_RATIO': 'Loan amount is high relative to income',
            'ANNUITY_INCOME_RATIO': 'Monthly payment burden is high relative to income',
            'DAYS_EMPLOYED': 'Length of current employment is shorter than typical',
            'YEARS_EMPLOYED': 'Employment history is shorter than typical',
            'AGE': 'Age is outside typical approved range',
            'AMT_CREDIT': 'Requested credit amount is higher than typical',
            'DAYS_BIRTH': 'Age factor is outside typical approved range',
            'BUREAU_DAYS_CREDIT': 'Credit history length is shorter than typical',
            'BUREAU_CREDIT_ACTIVE': 'Number of active credit accounts is concerning',
            'BUREAU_AMT_CREDIT_SUM_DEBT': 'Total existing debt is higher than typical',
            'CODE_GENDER': 'Demographic factors differ from typical profile',
            'REGION_RATING': 'Regional risk factors are higher than average',
            'ORGANIZATION_TYPE': 'Employment type has higher risk than typical'
        }
        
        # Find matching reason
        for key, reason in reason_mapping.items():
            if key in feature.upper():
                return reason
        
        # Default reason
        return f"{feature.replace('_', ' ').title()} is outside typical approved range"
    
    def plot_summary(self, X: pd.DataFrame, save_path: Optional[str] = None) -> None:
        """
        Generate SHAP summary plot showing global feature importance and impact.
        
        Args:
            X: Features
            save_path: Path to save plot
        """
        if self.shap_values is None:
            self.compute_shap_values(X)
        
        plt.figure(figsize=(12, 8))
        shap.summary_plot(
            self.shap_values,
            X.iloc[:len(self.shap_values)],
            feature_names=self.feature_names,
            max_display=20,
            show=False
        )
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"SHAP summary plot saved to {save_path}")
        else:
            plt.show()
        
        plt.close()
    
    def plot_waterfall(self, X: pd.DataFrame, instance_idx: int,
                      save_path: Optional[str] = None) -> None:
        """
        Generate waterfall plot for single instance explanation.
        
        Args:
            X: Features
            instance_idx: Index of instance
            save_path: Path to save plot
        """
        if self.shap_values is None:
            self.compute_shap_values(X)
        
        # Create explanation object
        shap_explanation = shap.Explanation(
            values=self.shap_values[instance_idx],
            base_values=self.base_value,
            data=X.iloc[instance_idx].values,
            feature_names=self.feature_names
        )
        
        plt.figure(figsize=(12, 8))
        shap.waterfall_plot(shap_explanation, show=False)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Waterfall plot saved to {save_path}")
        else:
            plt.show()
        
        plt.close()
    
    def plot_force(self, X: pd.DataFrame, instance_idx: int,
                  save_path: Optional[str] = None) -> None:
        """
        Generate force plot for single instance.
        
        Args:
            X: Features
            instance_idx: Index of instance
            save_path: Path to save plot (HTML format)
        """
        if self.shap_values is None:
            self.compute_shap_values(X)
        
        force_plot = shap.force_plot(
            self.base_value,
            self.shap_values[instance_idx],
            X.iloc[instance_idx],
            feature_names=self.feature_names
        )
        
        if save_path:
            shap.save_html(save_path, force_plot)
            logger.info(f"Force plot saved to {save_path}")
        else:
            return force_plot
    
    def plot_dependence(self, X: pd.DataFrame, feature: str,
                       interaction_feature: Optional[str] = None,
                       save_path: Optional[str] = None) -> None:
        """
        Generate dependence plot showing relationship between feature and SHAP value.
        
        Args:
            X: Features
            feature: Feature to plot
            interaction_feature: Feature to use for coloring (auto-detect if None)
            save_path: Path to save plot
        """
        if self.shap_values is None:
            self.compute_shap_values(X)
        
        plt.figure(figsize=(10, 6))
        shap.dependence_plot(
            feature,
            self.shap_values,
            X.iloc[:len(self.shap_values)],
            interaction_index=interaction_feature,
            show=False
        )
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Dependence plot saved to {save_path}")
        else:
            plt.show()
        
        plt.close()
    
    def save_explainer(self, save_dir: str = "models", name: str = "explainer") -> None:
        """Save explainer artifacts."""
        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)
        
        artifacts = {
            'feature_names': self.feature_names,
            'base_value': self.base_value
        }
        
        joblib.dump(artifacts, save_path / f"{name}_artifacts.pkl")
        logger.info(f"Explainer artifacts saved to {save_path}")
    
    def generate_explanation_report(self, X: pd.DataFrame, instance_idx: int,
                                   prediction_proba: float) -> Dict[str, Any]:
        """
        Generate comprehensive explanation report for an instance.
        
        Args:
            X: Features
            instance_idx: Index of instance
            prediction_proba: Model's predicted probability
            
        Returns:
            Dictionary with complete explanation
        """
        explanation = self.explain_instance(X, instance_idx)
        adverse_reasons = self.generate_adverse_action_reasons(X, instance_idx)
        
        report = {
            'instance_id': instance_idx,
            'predicted_probability': prediction_proba,
            'base_probability': explanation['base_value'],
            'top_positive_factors': [f for f in explanation['top_features'] if f['shap_value'] > 0][:3],
            'top_negative_factors': [f for f in explanation['top_features'] if f['shap_value'] < 0][:3],
            'adverse_action_reasons': adverse_reasons
        }
        
        return report


if __name__ == "__main__":
    logger.info("SHAP Explainability module loaded successfully")
