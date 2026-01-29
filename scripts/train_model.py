"""
End-to-End Training Pipeline for Credit Risk Model
Orchestrates data loading, feature engineering, model training, and validation
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from loguru import logger
import warnings
warnings.filterwarnings('ignore')

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from data.data_loader import DataLoader, DataPreprocessor
from features.feature_engineering import FeatureEngineer
from model.model_training import CreditRiskModel
from model.decision_engine import DecisionEngine
from explainability.shap_explainer import ModelExplainer
from fairness.fairness_analyzer import FairnessAnalyzer
from monitoring.drift_detection import ModelMonitor


def main():
    """
    Execute complete training pipeline.
    """
    logger.info("="*70)
    logger.info("CREDIT RISK MODEL TRAINING PIPELINE")
    logger.info("="*70)
    
    # ==================== STEP 1: DATA LOADING ====================
    logger.info("\n[STEP 1] Loading Data...")
    
    loader = DataLoader()
    
    try:
        df_train = loader.load_application_train()
    except FileNotFoundError:
        logger.error("Training data not found. Please download Home Credit dataset.")
        logger.info("Download from: https://www.kaggle.com/c/home-credit-default-risk/data")
        logger.info("Or use: loader.download_kaggle_dataset()")
        return
    
    # Get data summary
    summary = loader.get_data_summary(df_train)
    logger.info(f"Loaded {summary['n_rows']:,} applications")
    logger.info(f"Default rate: {summary.get('default_rate', 0):.2%}")
    
    # ==================== STEP 2: DATA PREPROCESSING ====================
    logger.info("\n[STEP 2] Preprocessing Data...")
    
    preprocessor = DataPreprocessor()
    df_clean = preprocessor.clean_data(df_train)
    df_clean = preprocessor.remove_duplicates(df_clean)
    df_clean = preprocessor.handle_missing_values(df_clean)
    
    logger.info(f"Cleaned data shape: {df_clean.shape}")
    
    # ==================== STEP 3: FEATURE ENGINEERING ====================
    logger.info("\n[STEP 3] Engineering Features...")
    
    engineer = FeatureEngineer()
    
    # Create application features
    df_features = engineer.create_application_features(df_clean)
    
    # Load and merge bureau features (if available)
    try:
        bureau, bureau_balance = loader.load_bureau_data()
        if not bureau.empty:
            df_features = engineer.create_bureau_features(df_features, bureau, bureau_balance)
    except Exception as e:
        logger.warning(f"Could not load bureau data: {e}")
    
    # Encode categorical features
    df_encoded = engineer.encode_categorical_features(df_features, fit=True)
    
    # Select features
    feature_cols = engineer.select_features(df_encoded, target_col='TARGET')
    
    logger.info(f"Selected {len(feature_cols)} features for modeling")
    
    # Save feature engineering artifacts
    engineer.save_artifacts(save_dir="models")
    
    # ==================== STEP 4: MODEL TRAINING ====================
    logger.info("\n[STEP 4] Training Model...")
    
    model = CreditRiskModel()
    
    # Prepare data
    X, y, ids = model.prepare_data(df_encoded[feature_cols + ['TARGET', 'SK_ID_CURR']])
    
    # Split data
    X_train, X_val, y_train, y_val = model.split_data(X, y)
    
    # Train model
    model.train(X_train, y_train, X_val, y_val)
    
    # Calibrate model
    model.calibrate(X_train, y_train)
    
    # ==================== STEP 5: MODEL EVALUATION ====================
    logger.info("\n[STEP 5] Evaluating Model...")
    
    # Evaluate on training set
    train_metrics = model.evaluate(X_train, y_train, dataset_name="training")
    
    # Evaluate on validation set
    val_metrics = model.evaluate(X_val, y_val, dataset_name="validation")
    
    # Cross-validation
    cv_results = model.cross_validate(X_train, y_train)
    
    # Generate performance plots
    logger.info("Generating performance plots...")
    model.plot_model_performance(X_val, y_val, save_path="models/model_performance.png")
    
    # Save model
    model.save_model(save_dir="models")
    
    logger.info("\nModel Performance Summary:")
    logger.info(f"  Training AUC: {train_metrics['auc']:.4f}")
    logger.info(f"  Validation AUC: {val_metrics['auc']:.4f}")
    logger.info(f"  CV AUC: {cv_results['mean_auc']:.4f} (+/- {cv_results['std_auc']:.4f})")
    logger.info(f"  Gini Coefficient: {val_metrics['gini']:.4f}")
    logger.info(f"  KS Statistic: {val_metrics['ks_statistic']:.4f}")
    
    # ==================== STEP 6: EXPLAINABILITY ====================
    logger.info("\n[STEP 6] Computing Explainability...")
    
    # Sample for SHAP (computation intensive)
    X_shap = X_val.sample(n=min(1000, len(X_val)), random_state=42)
    y_shap = y_val.loc[X_shap.index]
    
    explainer = ModelExplainer(
        model.calibrated_model if model.calibrated_model else model.model,
        X_train.sample(n=100, random_state=42)
    )
    
    # Compute SHAP values
    shap_values = explainer.compute_shap_values(X_shap)
    
    # Get global importance
    global_importance = explainer.get_global_importance(X_shap, top_n=20)
    logger.info("\nTop 10 Most Important Features (SHAP):")
    for idx, row in global_importance.head(10).iterrows():
        logger.info(f"  {row['feature']}: {row['importance']:.4f}")
    
    # Generate SHAP plots
    logger.info("Generating SHAP plots...")
    explainer.plot_summary(X_shap, save_path="models/shap_summary.png")
    
    # Save explainer
    explainer.save_explainer(save_dir="models")
    
    # ==================== STEP 7: FAIRNESS ANALYSIS ====================
    logger.info("\n[STEP 7] Analyzing Fairness...")
    
    # Prepare data for fairness analysis
    df_fairness = X_val.copy()
    df_fairness['TARGET'] = y_val
    df_fairness['predicted_proba'] = model.predict_proba(X_val)
    
    # Add proxy features if they exist
    for col in ['CODE_GENDER', 'AGE_GROUP', 'REGION_RATING_CLIENT']:
        if col in df_encoded.columns:
            df_fairness[col] = df_encoded.loc[df_fairness.index, col]
    
    fairness_analyzer = FairnessAnalyzer()
    fairness_results = fairness_analyzer.analyze_fairness(
        df_fairness,
        y_true_col='TARGET',
        y_score_col='predicted_proba',
        threshold=0.15
    )
    
    # Detect biases
    biases = fairness_analyzer.detect_bias()
    
    # Generate fairness report
    fairness_report = fairness_analyzer.generate_fairness_report(
        save_path="models/fairness_report.csv"
    )
    
    # Get recommendations
    recommendations = fairness_analyzer.get_mitigation_recommendations()
    logger.info("\nFairness Recommendations:")
    for rec in recommendations:
        logger.info(f"  {rec}")
    
    # ==================== STEP 8: DECISION ENGINE ====================
    logger.info("\n[STEP 8] Testing Decision Engine...")
    
    decision_engine = DecisionEngine()
    
    # Make batch decisions
    df_decisions = df_fairness.copy()
    decisions_df = decision_engine.batch_decisions(
        df_decisions,
        pd_col='predicted_proba',
        include_application_data=True
    )
    
    # Get decision distribution
    decision_dist = decision_engine.get_decision_distribution(decisions_df)
    
    # ==================== STEP 9: MONITORING SETUP ====================
    logger.info("\n[STEP 9] Setting Up Monitoring...")
    
    monitor = ModelMonitor()
    
    # Set baseline from training data
    monitor.set_baseline(X_train, feature_cols)
    
    # Test drift detection on validation set
    drift_results = monitor.detect_feature_drift(X_val, feature_cols)
    
    # Check retraining trigger
    should_retrain, reasons = monitor.check_retraining_trigger(drift_results, val_metrics)
    
    # Save monitoring state
    monitor.save_monitoring_state(save_dir="models")
    
    # ==================== FINAL SUMMARY ====================
    logger.info("\n" + "="*70)
    logger.info("TRAINING PIPELINE COMPLETED SUCCESSFULLY")
    logger.info("="*70)
    
    logger.info("\n📊 MODEL PERFORMANCE:")
    logger.info(f"  • AUC-ROC: {val_metrics['auc']:.4f}")
    logger.info(f"  • Gini: {val_metrics['gini']:.4f}")
    logger.info(f"  • KS Statistic: {val_metrics['ks_statistic']:.4f}")
    
    logger.info("\n🎯 DECISION METRICS:")
    logger.info(f"  • Approval Rate: {decision_dist['approval_rate']:.2%}")
    logger.info(f"  • Rejection Rate: {decision_dist['rejection_rate']:.2%}")
    if 'approved_stats' in decision_dist:
        logger.info(f"  • Avg Credit Limit: ${decision_dist['approved_stats']['avg_credit_limit']:,.0f}")
        logger.info(f"  • Avg Interest Rate: {decision_dist['approved_stats']['avg_interest_rate']:.2f}%")
    
    logger.info("\n⚖️ FAIRNESS:")
    logger.info(f"  • High Concern Items: {len(biases['high_concern'])}")
    logger.info(f"  • Moderate Concern Items: {len(biases['moderate_concern'])}")
    logger.info(f"  • Acceptable Items: {len(biases['acceptable'])}")
    
    logger.info("\n📁 ARTIFACTS SAVED:")
    logger.info("  • models/credit_risk_model_*.pkl")
    logger.info("  • models/*_features.pkl, *_encoders.pkl")
    logger.info("  • models/model_performance.png")
    logger.info("  • models/shap_summary.png")
    logger.info("  • models/fairness_report.csv")
    logger.info("  • models/monitoring_state.pkl")
    
    logger.info("\n🚀 NEXT STEPS:")
    logger.info("  1. Review model performance plots")
    logger.info("  2. Check fairness report for biases")
    logger.info("  3. Deploy API: python src/api/api_service.py")
    logger.info("  4. Test API: python scripts/test_api.py")
    
    logger.info("\n" + "="*70)


if __name__ == "__main__":
    main()
