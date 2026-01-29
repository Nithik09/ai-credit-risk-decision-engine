"""
Credit Risk Engine
Production-grade AI credit risk system with PD modeling, explainability, fairness, and MLOps
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from src.data import DataLoader, DataPreprocessor
from src.features import FeatureEngineer
from src.model import CreditRiskModel, DecisionEngine
from src.explainability import ModelExplainer
from src.fairness import FairnessAnalyzer
from src.monitoring import ModelMonitor

__all__ = [
    'DataLoader',
    'DataPreprocessor',
    'FeatureEngineer',
    'CreditRiskModel',
    'DecisionEngine',
    'ModelExplainer',
    'FairnessAnalyzer',
    'ModelMonitor'
]
