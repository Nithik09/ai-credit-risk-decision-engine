"""
Feature Engineering Module for Credit Risk Modeling
Creates domain-specific features for credit risk assessment
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from loguru import logger
import yaml
from sklearn.preprocessing import LabelEncoder, StandardScaler
import joblib


class FeatureEngineer:
    """
    Creates advanced features for credit risk modeling.
    
    Implements:
    - Domain-specific credit features
    - Aggregations from bureau data
    - Interaction features
    - Feature encoding and scaling
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize feature engineer with configuration."""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.label_encoders = {}
        self.scaler = None
        self.feature_names = []
        
        logger.info("FeatureEngineer initialized")
    
    def create_application_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create features from main application data.
        
        Args:
            df: Application DataFrame
            
        Returns:
            DataFrame with engineered features
        """
        logger.info("Engineering application features...")
        df_feat = df.copy()
        
        # ==================== CREDIT BEHAVIOR FEATURES ====================
        
        # Credit-to-income ratio (key credit risk indicator)
        if 'AMT_CREDIT' in df_feat.columns and 'AMT_INCOME_TOTAL' in df_feat.columns:
            df_feat['CREDIT_INCOME_RATIO'] = df_feat['AMT_CREDIT'] / (df_feat['AMT_INCOME_TOTAL'] + 1)
            df_feat['CREDIT_INCOME_RATIO'] = df_feat['CREDIT_INCOME_RATIO'].clip(0, 10)  # Cap at 10x
        
        # Annuity-to-income ratio (payment burden)
        if 'AMT_ANNUITY' in df_feat.columns and 'AMT_INCOME_TOTAL' in df_feat.columns:
            df_feat['ANNUITY_INCOME_RATIO'] = df_feat['AMT_ANNUITY'] / (df_feat['AMT_INCOME_TOTAL'] + 1)
            df_feat['PAYMENT_BURDEN'] = df_feat['ANNUITY_INCOME_RATIO'].apply(
                lambda x: 'High' if x > 0.4 else ('Medium' if x > 0.25 else 'Low')
            )
        
        # Loan term (credit duration in months)
        if 'AMT_CREDIT' in df_feat.columns and 'AMT_ANNUITY' in df_feat.columns:
            df_feat['LOAN_TERM_MONTHS'] = (df_feat['AMT_CREDIT'] / (df_feat['AMT_ANNUITY'] + 1)).clip(0, 600)
        
        # Income per family member
        if 'AMT_INCOME_TOTAL' in df_feat.columns and 'CNT_FAM_MEMBERS' in df_feat.columns:
            df_feat['INCOME_PER_PERSON'] = df_feat['AMT_INCOME_TOTAL'] / (df_feat['CNT_FAM_MEMBERS'] + 1)
        
        # ==================== DEMOGRAPHIC FEATURES ====================
        
        # Employment stability
        if 'DAYS_EMPLOYED' in df_feat.columns:
            df_feat['YEARS_EMPLOYED'] = (-df_feat['DAYS_EMPLOYED'] / 365).clip(0, 65)
            df_feat['EMPLOYMENT_STABILITY'] = pd.cut(
                df_feat['YEARS_EMPLOYED'],
                bins=[-1, 1, 3, 5, 10, 100],
                labels=['New', 'Recent', 'Stable', 'Senior', 'Very_Senior']
            )
        
        # Age features
        if 'DAYS_BIRTH' in df_feat.columns:
            df_feat['AGE'] = (-df_feat['DAYS_BIRTH'] / 365).round(1)
            df_feat['AGE_SQUARED'] = df_feat['AGE'] ** 2  # Non-linear age effect
        
        # Days since registration
        if 'DAYS_REGISTRATION' in df_feat.columns:
            df_feat['YEARS_REGISTRATION'] = (-df_feat['DAYS_REGISTRATION'] / 365).clip(0, 100)
        
        # Days since ID publish
        if 'DAYS_ID_PUBLISH' in df_feat.columns:
            df_feat['YEARS_ID_PUBLISH'] = (-df_feat['DAYS_ID_PUBLISH'] / 365).clip(0, 100)
        
        # ==================== ASSET & WEALTH FEATURES ====================
        
        # Car age
        if 'OWN_CAR_AGE' in df_feat.columns:
            df_feat['OWN_CAR_AGE'].fillna(-1, inplace=True)  # -1 indicates no car
            df_feat['HAS_CAR'] = (df_feat['OWN_CAR_AGE'] >= 0).astype(int)
        
        # External source combinations (credit bureau scores)
        ext_sources = ['EXT_SOURCE_1', 'EXT_SOURCE_2', 'EXT_SOURCE_3']
        if all(col in df_feat.columns for col in ext_sources):
            # Mean external score
            df_feat['EXT_SOURCE_MEAN'] = df_feat[ext_sources].mean(axis=1)
            # Max external score
            df_feat['EXT_SOURCE_MAX'] = df_feat[ext_sources].max(axis=1)
            # Min external score
            df_feat['EXT_SOURCE_MIN'] = df_feat[ext_sources].min(axis=1)
            # Standard deviation (volatility across bureaus)
            df_feat['EXT_SOURCE_STD'] = df_feat[ext_sources].std(axis=1)
            # Weighted combination (EXT_SOURCE_2 is often most predictive)
            df_feat['EXT_SOURCE_WEIGHTED'] = (
                0.2 * df_feat['EXT_SOURCE_1'].fillna(0.5) +
                0.5 * df_feat['EXT_SOURCE_2'].fillna(0.5) +
                0.3 * df_feat['EXT_SOURCE_3'].fillna(0.5)
            )
        
        # ==================== DOCUMENT FLAGS ====================
        
        # Count of provided documents
        doc_cols = [col for col in df_feat.columns if 'FLAG_DOCUMENT' in col]
        if doc_cols:
            df_feat['DOCUMENT_COUNT'] = df_feat[doc_cols].sum(axis=1)
        
        # ==================== INTERACTION FEATURES ====================
        
        # Income × External Score
        if 'AMT_INCOME_TOTAL' in df_feat.columns and 'EXT_SOURCE_MEAN' in df_feat.columns:
            df_feat['INCOME_CREDIT_SCORE'] = df_feat['AMT_INCOME_TOTAL'] * df_feat['EXT_SOURCE_MEAN']
        
        # Age × Employment
        if 'AGE' in df_feat.columns and 'YEARS_EMPLOYED' in df_feat.columns:
            df_feat['AGE_EMPLOYMENT_RATIO'] = df_feat['AGE'] / (df_feat['YEARS_EMPLOYED'] + 1)
        
        logger.info(f"Created {len(df_feat.columns) - len(df.columns)} new features")
        return df_feat
    
    def create_bureau_features(self, df: pd.DataFrame, bureau: pd.DataFrame, 
                               bureau_balance: pd.DataFrame) -> pd.DataFrame:
        """
        Create aggregated features from bureau credit history.
        
        Args:
            df: Main application DataFrame
            bureau: Bureau data (past loans)
            bureau_balance: Bureau balance data (monthly credit bureau history)
            
        Returns:
            DataFrame with bureau aggregation features
        """
        logger.info("Creating bureau features...")
        
        if bureau.empty:
            logger.warning("Bureau data is empty, skipping bureau features")
            return df
        
        # ==================== BUREAU AGGREGATIONS ====================
        
        bureau_agg = bureau.groupby('SK_ID_CURR').agg({
            'DAYS_CREDIT': ['min', 'max', 'mean'],  # Credit history length
            'CREDIT_DAY_OVERDUE': ['max', 'mean'],  # Overdue days
            'DAYS_CREDIT_ENDDATE': ['min', 'max', 'mean'],
            'AMT_CREDIT_MAX_OVERDUE': ['max', 'mean'],  # Maximum overdue amount
            'AMT_CREDIT_SUM': ['sum', 'mean', 'max'],  # Total credit amount
            'AMT_CREDIT_SUM_DEBT': ['sum', 'mean', 'max'],  # Current debt
            'AMT_CREDIT_SUM_OVERDUE': ['sum', 'mean', 'max'],  # Overdue amount
            'AMT_ANNUITY': ['mean', 'max'],
            'CREDIT_ACTIVE': lambda x: (x == 'Active').sum(),  # Count of active credits
            'CREDIT_TYPE': 'count'  # Total number of past credits
        })
        
        # Flatten multi-level columns
        bureau_agg.columns = ['BUREAU_' + '_'.join(col).strip().upper() for col in bureau_agg.columns.values]
        bureau_agg.reset_index(inplace=True)
        
        # Additional bureau features
        bureau_agg['BUREAU_CREDIT_ACTIVE_RATIO'] = (
            bureau_agg['BUREAU_CREDIT_ACTIVE'] / (bureau_agg['BUREAU_CREDIT_TYPE_COUNT'] + 1)
        )
        
        # Debt-to-credit ratio
        if 'BUREAU_AMT_CREDIT_SUM_DEBT_SUM' in bureau_agg.columns and 'BUREAU_AMT_CREDIT_SUM_SUM' in bureau_agg.columns:
            bureau_agg['BUREAU_DEBT_CREDIT_RATIO'] = (
                bureau_agg['BUREAU_AMT_CREDIT_SUM_DEBT_SUM'] / 
                (bureau_agg['BUREAU_AMT_CREDIT_SUM_SUM'] + 1)
            )
        
        # Overdue ratio
        if 'BUREAU_AMT_CREDIT_SUM_OVERDUE_SUM' in bureau_agg.columns and 'BUREAU_AMT_CREDIT_SUM_SUM' in bureau_agg.columns:
            bureau_agg['BUREAU_OVERDUE_RATIO'] = (
                bureau_agg['BUREAU_AMT_CREDIT_SUM_OVERDUE_SUM'] / 
                (bureau_agg['BUREAU_AMT_CREDIT_SUM_SUM'] + 1)
            )
        
        # ==================== BUREAU BALANCE FEATURES ====================
        
        if not bureau_balance.empty:
            # Merge bureau_balance with bureau to get SK_ID_CURR
            bb = bureau_balance.merge(bureau[['SK_ID_BUREAU', 'SK_ID_CURR']], on='SK_ID_BUREAU', how='left')
            
            bb_agg = bb.groupby('SK_ID_CURR').agg({
                'MONTHS_BALANCE': ['min', 'max'],
                'STATUS': lambda x: (x == 'C').sum()  # Count of completed statuses
            })
            
            bb_agg.columns = ['BB_' + '_'.join(col).strip().upper() for col in bb_agg.columns.values]
            bb_agg.reset_index(inplace=True)
            
            # Merge bureau balance features
            bureau_agg = bureau_agg.merge(bb_agg, on='SK_ID_CURR', how='left')
        
        # Merge with main dataframe
        df_merged = df.merge(bureau_agg, on='SK_ID_CURR', how='left')
        
        logger.info(f"Added {len(bureau_agg.columns) - 1} bureau features")
        return df_merged
    
    def encode_categorical_features(self, df: pd.DataFrame, fit: bool = True) -> pd.DataFrame:
        """
        Encode categorical variables using label encoding and one-hot encoding.
        
        Args:
            df: Input DataFrame
            fit: Whether to fit encoders (True for train, False for test)
            
        Returns:
            DataFrame with encoded features
        """
        logger.info("Encoding categorical features...")
        df_encoded = df.copy()
        
        categorical_cols = df_encoded.select_dtypes(include=['object', 'category']).columns
        categorical_cols = [col for col in categorical_cols if col not in ['SK_ID_CURR', 'TARGET']]
        
        max_cardinality = self.config['feature_engineering']['max_categorical_cardinality']
        
        for col in categorical_cols:
            n_unique = df_encoded[col].nunique()
            
            if n_unique <= 2:
                # Binary encoding
                if fit:
                    self.label_encoders[col] = LabelEncoder()
                    df_encoded[col] = self.label_encoders[col].fit_transform(df_encoded[col].astype(str))
                else:
                    if col in self.label_encoders:
                        df_encoded[col] = self.label_encoders[col].transform(df_encoded[col].astype(str))
                
            elif n_unique <= max_cardinality:
                # One-hot encoding for low cardinality
                dummies = pd.get_dummies(df_encoded[col], prefix=col, drop_first=True)
                df_encoded = pd.concat([df_encoded, dummies], axis=1)
                df_encoded.drop(col, axis=1, inplace=True)
            
            else:
                # Label encoding for high cardinality
                if fit:
                    self.label_encoders[col] = LabelEncoder()
                    df_encoded[col] = self.label_encoders[col].fit_transform(df_encoded[col].astype(str))
                else:
                    if col in self.label_encoders:
                        # Handle unseen categories
                        df_encoded[col] = df_encoded[col].apply(
                            lambda x: x if x in self.label_encoders[col].classes_ else 'Unknown'
                        )
                        df_encoded[col] = self.label_encoders[col].transform(df_encoded[col].astype(str))
        
        logger.info(f"Encoded {len(categorical_cols)} categorical features")
        return df_encoded
    
    def select_features(self, df: pd.DataFrame, target_col: str = 'TARGET',
                       importance_threshold: Optional[float] = None) -> List[str]:
        """
        Select features based on correlation and importance.
        
        Args:
            df: Input DataFrame with target
            target_col: Name of target column
            importance_threshold: Minimum feature importance to keep
            
        Returns:
            List of selected feature names
        """
        logger.info("Selecting features...")
        
        # Exclude ID and target
        feature_cols = [col for col in df.columns if col not in ['SK_ID_CURR', target_col]]
        
        # Remove features with too many missing values (>90%)
        missing_pct = df[feature_cols].isnull().mean()
        high_missing = missing_pct[missing_pct > 0.9].index.tolist()
        feature_cols = [col for col in feature_cols if col not in high_missing]
        
        if high_missing:
            logger.info(f"Removed {len(high_missing)} features with >90% missing values")
        
        # Remove highly correlated features
        numeric_cols = df[feature_cols].select_dtypes(include=['number']).columns.tolist()
        if len(numeric_cols) > 0:
            corr_matrix = df[numeric_cols].corr().abs()
            upper_triangle = corr_matrix.where(
                np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
            )
            
            corr_threshold = self.config['feature_engineering']['correlation_threshold']
            to_drop = [col for col in upper_triangle.columns if any(upper_triangle[col] > corr_threshold)]
            
            feature_cols = [col for col in feature_cols if col not in to_drop]
            
            if to_drop:
                logger.info(f"Removed {len(to_drop)} highly correlated features (>{corr_threshold})")
        
        # Remove zero-variance features
        zero_var = df[feature_cols].std() == 0
        zero_var_cols = zero_var[zero_var].index.tolist()
        feature_cols = [col for col in feature_cols if col not in zero_var_cols]
        
        if zero_var_cols:
            logger.info(f"Removed {len(zero_var_cols)} zero-variance features")
        
        logger.info(f"Selected {len(feature_cols)} features for modeling")
        self.feature_names = feature_cols
        
        return feature_cols
    
    def scale_features(self, df: pd.DataFrame, feature_cols: List[str], fit: bool = True) -> pd.DataFrame:
        """
        Scale numeric features using StandardScaler.
        
        Args:
            df: Input DataFrame
            feature_cols: List of feature columns to scale
            fit: Whether to fit scaler (True for train, False for test)
            
        Returns:
            DataFrame with scaled features
        """
        logger.info("Scaling features...")
        df_scaled = df.copy()
        
        numeric_cols = df_scaled[feature_cols].select_dtypes(include=['number']).columns.tolist()
        
        if fit:
            self.scaler = StandardScaler()
            df_scaled[numeric_cols] = self.scaler.fit_transform(df_scaled[numeric_cols])
        else:
            if self.scaler is not None:
                df_scaled[numeric_cols] = self.scaler.transform(df_scaled[numeric_cols])
        
        return df_scaled
    
    def save_artifacts(self, save_dir: str = "models") -> None:
        """Save feature engineering artifacts (encoders, scaler, feature names)."""
        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)
        
        joblib.dump(self.label_encoders, save_path / "label_encoders.pkl")
        joblib.dump(self.scaler, save_path / "scaler.pkl")
        joblib.dump(self.feature_names, save_path / "feature_names.pkl")
        
        logger.info(f"Feature engineering artifacts saved to {save_path}")
    
    def load_artifacts(self, load_dir: str = "models") -> None:
        """Load feature engineering artifacts."""
        load_path = Path(load_dir)
        
        self.label_encoders = joblib.load(load_path / "label_encoders.pkl")
        self.scaler = joblib.load(load_path / "scaler.pkl")
        self.feature_names = joblib.load(load_path / "feature_names.pkl")
        
        logger.info(f"Feature engineering artifacts loaded from {load_path}")


if __name__ == "__main__":
    # Example usage
    from data_loader import DataLoader
    
    loader = DataLoader()
    df = loader.load_application_train()
    
    engineer = FeatureEngineer()
    df_feat = engineer.create_application_features(df)
    
    print(f"Original features: {len(df.columns)}")
    print(f"Engineered features: {len(df_feat.columns)}")
