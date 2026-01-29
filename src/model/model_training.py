"""
Credit Risk Model Training & Calibration Module
Implements production-grade PD model with proper calibration and validation
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional, Any
from pathlib import Path
import yaml
import joblib
from loguru import logger

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import (
    roc_auc_score, roc_curve, precision_recall_curve, 
    classification_report, confusion_matrix, brier_score_loss
)
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
import lightgbm as lgb
import xgboost as xgb

import matplotlib.pyplot as plt
import seaborn as sns


class CreditRiskModel:
    """
    Production-grade credit risk model with calibration and validation.
    
    Key Features:
    - LightGBM/XGBoost for PD prediction
    - Probability calibration (Platt/Isotonic)
    - Comprehensive model evaluation (AUC, KS, Gini)
    - Cross-validation
    - Model persistence
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize model with configuration."""
        # Handle relative path from different execution contexts
        if not Path(config_path).exists():
            root_config = Path(__file__).parent.parent.parent / config_path
            if root_config.exists():
                config_path = str(root_config)
        
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.model = None
        self.calibrated_model = None
        self.feature_names = []
        self.feature_importance = None
        self.training_metrics = {}
        self.validation_metrics = {}
        
        logger.info("CreditRiskModel initialized")
    
    def prepare_data(self, df: pd.DataFrame, target_col: str = 'TARGET',
                    id_col: str = 'SK_ID_CURR') -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
        """
        Prepare data for modeling.
        
        Args:
            df: Input DataFrame with features and target
            target_col: Target column name
            id_col: ID column name
            
        Returns:
            Tuple of (X, y, ids)
        """
        logger.info("Preparing data for modeling...")
        
        # Separate features, target, and IDs
        exclude_cols = [target_col, id_col]
        feature_cols = [col for col in df.columns if col not in exclude_cols]
        
        X = df[feature_cols].copy()
        y = df[target_col].copy()
        ids = df[id_col].copy()
        
        # Handle any remaining missing values
        X.fillna(X.median(numeric_only=True), inplace=True)
        
        # Ensure all features are numeric
        non_numeric = X.select_dtypes(exclude=['number']).columns
        if len(non_numeric) > 0:
            logger.warning(f"Non-numeric columns found: {non_numeric.tolist()}")
            X = X.select_dtypes(include=['number'])
        
        self.feature_names = X.columns.tolist()
        logger.info(f"Prepared {len(self.feature_names)} features for {len(X)} samples")
        logger.info(f"Target distribution: {y.value_counts().to_dict()}")
        
        return X, y, ids
    
    def split_data(self, X: pd.DataFrame, y: pd.Series, 
                   test_size: float = None, random_state: int = 42) -> Tuple:
        """
        Split data into train and validation sets with stratification.
        
        Args:
            X: Feature matrix
            y: Target vector
            test_size: Proportion of data for validation
            random_state: Random seed
            
        Returns:
            Tuple of (X_train, X_val, y_train, y_val)
        """
        if test_size is None:
            test_size = self.config['model']['validation']['test_size']
        
        stratify = y if self.config['model']['validation']['stratify'] else None
        
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, 
            test_size=test_size,
            stratify=stratify,
            random_state=random_state
        )
        
        logger.info(f"Data split: Train={len(X_train):,}, Val={len(X_val):,}")
        logger.info(f"Train default rate: {y_train.mean():.4f}")
        logger.info(f"Val default rate: {y_val.mean():.4f}")
        
        return X_train, X_val, y_train, y_val
    
    def train(self, X_train: pd.DataFrame, y_train: pd.Series,
              X_val: Optional[pd.DataFrame] = None, 
              y_val: Optional[pd.Series] = None) -> None:
        """
        Train credit risk model.
        
        Args:
            X_train: Training features
            y_train: Training target
            X_val: Validation features (optional)
            y_val: Validation target (optional)
        """
        logger.info("Training credit risk model...")
        
        algorithm = self.config['model']['algorithm']
        params = self.config['model']['params'].copy()
        
        if algorithm == 'lightgbm':
            self.model = self._train_lightgbm(X_train, y_train, X_val, y_val, params)
        elif algorithm == 'xgboost':
            self.model = self._train_xgboost(X_train, y_train, X_val, y_val, params)
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
        
        # Extract feature importance
        self._extract_feature_importance()
        
        logger.info("Model training complete")
    
    def _train_lightgbm(self, X_train, y_train, X_val, y_val, params) -> lgb.LGBMClassifier:
        """Train LightGBM model."""
        model = lgb.LGBMClassifier(**params)
        
        eval_set = [(X_val, y_val)] if X_val is not None else None
        
        model.fit(
            X_train, y_train,
            eval_set=eval_set,
            eval_metric='auc',
            callbacks=[lgb.early_stopping(stopping_rounds=50, verbose=False)]
        )
        
        logger.info(f"LightGBM trained with {model.n_estimators} iterations")
        return model
    
    def _train_xgboost(self, X_train, y_train, X_val, y_val, params) -> xgb.XGBClassifier:
        """Train XGBoost model."""
        # Adapt params for XGBoost
        xgb_params = {
            'n_estimators': params.get('n_estimators', 500),
            'learning_rate': params.get('learning_rate', 0.05),
            'max_depth': params.get('max_depth', 7),
            'subsample': params.get('subsample', 0.8),
            'colsample_bytree': params.get('colsample_bytree', 0.8),
            'reg_alpha': params.get('reg_alpha', 0.1),
            'reg_lambda': params.get('reg_lambda', 0.1),
            'random_state': params.get('random_state', 42),
            'n_jobs': params.get('n_jobs', -1),
            'eval_metric': 'auc'
        }
        
        model = xgb.XGBClassifier(**xgb_params)
        
        eval_set = [(X_val, y_val)] if X_val is not None else None
        
        model.fit(
            X_train, y_train,
            eval_set=eval_set,
            verbose=False
        )
        
        logger.info(f"XGBoost trained")
        return model
    
    def calibrate(self, X_train: pd.DataFrame, y_train: pd.Series,
                  method: Optional[str] = None, cv: int = None) -> None:
        """
        Calibrate model probabilities using Platt scaling or Isotonic regression.
        
        Critical for credit risk: raw ML probabilities are often poorly calibrated.
        Calibration ensures P(default|score) is reliable for pricing and decisions.
        
        Args:
            X_train: Training features
            y_train: Training target
            method: 'sigmoid' (Platt) or 'isotonic'
            cv: Number of cross-validation folds
        """
        if method is None:
            method = self.config['model']['calibration']['method']
        if cv is None:
            cv = self.config['model']['calibration']['cv_folds']
        
        logger.info(f"Calibrating model using {method} method with {cv}-fold CV...")
        
        self.calibrated_model = CalibratedClassifierCV(
            self.model,
            method=method,
            cv=cv,
            n_jobs=-1
        )
        
        self.calibrated_model.fit(X_train, y_train)
        
        logger.info("Model calibration complete")
    
    def _extract_feature_importance(self) -> None:
        """Extract and store feature importance."""
        if hasattr(self.model, 'feature_importances_'):
            importance = self.model.feature_importances_
            self.feature_importance = pd.DataFrame({
                'feature': self.feature_names,
                'importance': importance
            }).sort_values('importance', ascending=False)
            
            logger.info(f"Top 5 features: {self.feature_importance.head()['feature'].tolist()}")
    
    def predict_proba(self, X: pd.DataFrame, calibrated: bool = True) -> np.ndarray:
        """
        Predict probability of default (PD).
        
        Args:
            X: Feature matrix
            calibrated: Use calibrated model if available
            
        Returns:
            Array of default probabilities
        """
        model = self.calibrated_model if (calibrated and self.calibrated_model) else self.model
        
        if model is None:
            raise ValueError("Model not trained yet")
        
        return model.predict_proba(X)[:, 1]
    
    def evaluate(self, X: pd.DataFrame, y: pd.Series, 
                dataset_name: str = "validation") -> Dict[str, float]:
        """
        Comprehensive model evaluation.
        
        Computes:
        - AUC-ROC
        - Kolmogorov-Smirnov (KS) statistic
        - Gini coefficient
        - Brier score (calibration quality)
        
        Args:
            X: Features
            y: True labels
            dataset_name: Name of dataset being evaluated
            
        Returns:
            Dictionary of metrics
        """
        logger.info(f"Evaluating model on {dataset_name} set...")
        
        # Get predictions
        y_pred_proba = self.predict_proba(X, calibrated=True)
        y_pred = (y_pred_proba > 0.5).astype(int)
        
        # AUC-ROC
        auc = roc_auc_score(y, y_pred_proba)
        
        # Gini coefficient (2*AUC - 1)
        gini = 2 * auc - 1
        
        # Kolmogorov-Smirnov statistic
        ks_stat = self._compute_ks_statistic(y, y_pred_proba)
        
        # Brier score (lower is better, measures calibration)
        brier = brier_score_loss(y, y_pred_proba)
        
        metrics = {
            'auc': auc,
            'gini': gini,
            'ks_statistic': ks_stat,
            'brier_score': brier,
            'default_rate': y.mean(),
            'n_samples': len(y)
        }
        
        # Store metrics
        if dataset_name == "training":
            self.training_metrics = metrics
        elif dataset_name == "validation":
            self.validation_metrics = metrics
        
        # Log metrics
        logger.info(f"{dataset_name.upper()} METRICS:")
        logger.info(f"  AUC: {auc:.4f}")
        logger.info(f"  Gini: {gini:.4f}")
        logger.info(f"  KS: {ks_stat:.4f}")
        logger.info(f"  Brier Score: {brier:.4f}")
        
        return metrics
    
    def _compute_ks_statistic(self, y_true: pd.Series, y_pred_proba: np.ndarray) -> float:
        """
        Compute Kolmogorov-Smirnov statistic.
        
        KS measures maximum separation between cumulative distributions of
        good and bad customers. Higher is better (0.3-0.4 is excellent).
        
        Args:
            y_true: True labels
            y_pred_proba: Predicted probabilities
            
        Returns:
            KS statistic
        """
        fpr, tpr, _ = roc_curve(y_true, y_pred_proba)
        ks = np.max(tpr - fpr)
        return ks
    
    def cross_validate(self, X: pd.DataFrame, y: pd.Series, cv: int = None) -> Dict[str, Any]:
        """
        Perform cross-validation.
        
        Args:
            X: Features
            y: Target
            cv: Number of folds
            
        Returns:
            Dictionary with CV results
        """
        if cv is None:
            cv = self.config['model']['validation']['cv_folds']
        
        logger.info(f"Performing {cv}-fold cross-validation...")
        
        skf = StratifiedKFold(n_splits=cv, shuffle=True, random_state=42)
        cv_scores = cross_val_score(self.model, X, y, cv=skf, scoring='roc_auc', n_jobs=-1)
        
        results = {
            'cv_scores': cv_scores,
            'mean_auc': cv_scores.mean(),
            'std_auc': cv_scores.std()
        }
        
        logger.info(f"CV AUC: {results['mean_auc']:.4f} (+/- {results['std_auc']:.4f})")
        
        return results
    
    def plot_model_performance(self, X_val: pd.DataFrame, y_val: pd.Series,
                              save_path: Optional[str] = None) -> None:
        """
        Generate comprehensive performance plots.
        
        Args:
            X_val: Validation features
            y_val: Validation target
            save_path: Path to save plots
        """
        y_pred_proba = self.predict_proba(X_val)
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # 1. ROC Curve
        fpr, tpr, _ = roc_curve(y_val, y_pred_proba)
        auc = roc_auc_score(y_val, y_pred_proba)
        
        axes[0, 0].plot(fpr, tpr, label=f'AUC = {auc:.4f}', linewidth=2)
        axes[0, 0].plot([0, 1], [0, 1], 'k--', label='Random')
        axes[0, 0].set_xlabel('False Positive Rate')
        axes[0, 0].set_ylabel('True Positive Rate')
        axes[0, 0].set_title('ROC Curve')
        axes[0, 0].legend()
        axes[0, 0].grid(alpha=0.3)
        
        # 2. Precision-Recall Curve
        precision, recall, _ = precision_recall_curve(y_val, y_pred_proba)
        
        axes[0, 1].plot(recall, precision, linewidth=2)
        axes[0, 1].set_xlabel('Recall')
        axes[0, 1].set_ylabel('Precision')
        axes[0, 1].set_title('Precision-Recall Curve')
        axes[0, 1].grid(alpha=0.3)
        
        # 3. Calibration Curve
        prob_true, prob_pred = calibration_curve(y_val, y_pred_proba, n_bins=10)
        
        axes[1, 0].plot(prob_pred, prob_true, marker='o', linewidth=2, label='Model')
        axes[1, 0].plot([0, 1], [0, 1], 'k--', label='Perfect Calibration')
        axes[1, 0].set_xlabel('Predicted Probability')
        axes[1, 0].set_ylabel('True Probability')
        axes[1, 0].set_title('Calibration Curve')
        axes[1, 0].legend()
        axes[1, 0].grid(alpha=0.3)
        
        # 4. Feature Importance (Top 20)
        if self.feature_importance is not None:
            top_features = self.feature_importance.head(20)
            axes[1, 1].barh(range(len(top_features)), top_features['importance'])
            axes[1, 1].set_yticks(range(len(top_features)))
            axes[1, 1].set_yticklabels(top_features['feature'])
            axes[1, 1].set_xlabel('Importance')
            axes[1, 1].set_title('Top 20 Feature Importances')
            axes[1, 1].invert_yaxis()
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Performance plots saved to {save_path}")
        else:
            plt.show()
        
        plt.close()
    
    def save_model(self, save_dir: str = "models", model_name: str = "credit_risk_model") -> None:
        """
        Save model and artifacts.
        
        Args:
            save_dir: Directory to save model
            model_name: Base name for model files
        """
        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)
        
        # Save base model
        joblib.dump(self.model, save_path / f"{model_name}_base.pkl")
        
        # Save calibrated model
        if self.calibrated_model:
            joblib.dump(self.calibrated_model, save_path / f"{model_name}_calibrated.pkl")
        
        # Save feature names
        joblib.dump(self.feature_names, save_path / f"{model_name}_features.pkl")
        
        # Save feature importance
        if self.feature_importance is not None:
            self.feature_importance.to_csv(save_path / f"{model_name}_feature_importance.csv", index=False)
        
        # Save metrics
        metrics = {
            'training': self.training_metrics,
            'validation': self.validation_metrics
        }
        joblib.dump(metrics, save_path / f"{model_name}_metrics.pkl")
        
        logger.info(f"Model saved to {save_path}")
    
    def load_model(self, load_dir: str = "models", model_name: str = "credit_risk_model") -> None:
        """
        Load model and artifacts.
        
        Args:
            load_dir: Directory containing model files
            model_name: Base name of model files
        """
        load_path = Path(load_dir)
        
        self.model = joblib.load(load_path / f"{model_name}_base.pkl")
        
        calibrated_path = load_path / f"{model_name}_calibrated.pkl"
        if calibrated_path.exists():
            self.calibrated_model = joblib.load(calibrated_path)
        
        self.feature_names = joblib.load(load_path / f"{model_name}_features.pkl")
        
        importance_path = load_path / f"{model_name}_feature_importance.csv"
        if importance_path.exists():
            self.feature_importance = pd.read_csv(importance_path)
        
        metrics_path = load_path / f"{model_name}_metrics.pkl"
        if metrics_path.exists():
            metrics = joblib.load(metrics_path)
            self.training_metrics = metrics.get('training', {})
            self.validation_metrics = metrics.get('validation', {})
        
        logger.info(f"Model loaded from {load_path}")


if __name__ == "__main__":
    logger.info("Credit Risk Model module loaded successfully")
