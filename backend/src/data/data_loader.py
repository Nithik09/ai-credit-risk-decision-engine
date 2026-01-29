"""
Data Loading Module for Credit Risk Engine
Handles downloading and loading Home Credit Default Risk dataset
"""

import os
import pandas as pd
from pathlib import Path
from typing import Dict, Tuple, Optional
from loguru import logger
import yaml


class DataLoader:
    """
    Loads and manages credit risk dataset from Home Credit Default Risk.
    
    This class handles:
    - Dataset downloading via Kaggle API
    - Data loading with memory optimization
    - Basic data validation
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize DataLoader with configuration.
        
        Args:
            config_path: Path to YAML configuration file
        """
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.raw_path = Path(self.config['data']['raw_path'])
        self.processed_path = Path(self.config['data']['processed_path'])
        
        # Create directories if they don't exist
        self.raw_path.mkdir(parents=True, exist_ok=True)
        self.processed_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"DataLoader initialized. Raw data: {self.raw_path}")
    
    def download_kaggle_dataset(self, competition: str = "home-credit-default-risk") -> None:
        """
        Download dataset from Kaggle using Kaggle API.
        
        Args:
            competition: Kaggle competition name
            
        Note:
            Requires kaggle.json in ~/.kaggle/ with API credentials
        """
        try:
            import kaggle
            logger.info(f"Downloading {competition} dataset from Kaggle...")
            
            kaggle.api.competition_download_files(
                competition, 
                path=str(self.raw_path),
                quiet=False
            )
            
            # Unzip files
            import zipfile
            zip_path = self.raw_path / f"{competition}.zip"
            if zip_path.exists():
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(self.raw_path)
                logger.info(f"Dataset extracted to {self.raw_path}")
                zip_path.unlink()  # Remove zip file
            
        except Exception as e:
            logger.error(f"Failed to download dataset: {e}")
            logger.info("Please manually download from: https://www.kaggle.com/c/home-credit-default-risk/data")
            raise
    
    def load_application_train(self, optimize_memory: bool = True) -> pd.DataFrame:
        """
        Load main training dataset with applicant information.
        
        Args:
            optimize_memory: Whether to optimize data types for memory efficiency
            
        Returns:
            DataFrame with application training data
        """
        file_path = self.raw_path / self.config['data']['train_file']
        
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            logger.info("Attempting to download dataset...")
            self.download_kaggle_dataset()
        
        logger.info(f"Loading {file_path}...")
        df = pd.read_csv(file_path)
        
        if optimize_memory:
            df = self._optimize_dtypes(df)
        
        logger.info(f"Loaded {len(df):,} applications with {df.shape[1]} features")
        logger.info(f"Target distribution: {df['TARGET'].value_counts().to_dict()}")
        
        return df
    
    def load_application_test(self, optimize_memory: bool = True) -> pd.DataFrame:
        """
        Load test dataset with applicant information.
        
        Args:
            optimize_memory: Whether to optimize data types for memory efficiency
            
        Returns:
            DataFrame with application test data
        """
        file_path = self.raw_path / self.config['data']['test_file']
        logger.info(f"Loading {file_path}...")
        df = pd.read_csv(file_path)
        
        if optimize_memory:
            df = self._optimize_dtypes(df)
        
        logger.info(f"Loaded {len(df):,} test applications")
        return df
    
    def load_bureau_data(self, optimize_memory: bool = True) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Load bureau and bureau_balance data (credit bureau history).
        
        Args:
            optimize_memory: Whether to optimize data types
            
        Returns:
            Tuple of (bureau_df, bureau_balance_df)
        """
        bureau_path = self.raw_path / self.config['data']['bureau_file']
        bureau_balance_path = self.raw_path / self.config['data']['bureau_balance_file']
        
        logger.info("Loading bureau data...")
        bureau = pd.read_csv(bureau_path) if bureau_path.exists() else pd.DataFrame()
        bureau_balance = pd.read_csv(bureau_balance_path) if bureau_balance_path.exists() else pd.DataFrame()
        
        if optimize_memory:
            bureau = self._optimize_dtypes(bureau)
            bureau_balance = self._optimize_dtypes(bureau_balance)
        
        logger.info(f"Bureau records: {len(bureau):,}")
        logger.info(f"Bureau balance records: {len(bureau_balance):,}")
        
        return bureau, bureau_balance
    
    def _optimize_dtypes(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Optimize DataFrame memory usage by downcasting numeric types.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Memory-optimized DataFrame
        """
        original_memory = df.memory_usage(deep=True).sum() / 1024**2
        
        # Optimize integers
        int_cols = df.select_dtypes(include=['int64']).columns
        for col in int_cols:
            df[col] = pd.to_numeric(df[col], downcast='integer')
        
        # Optimize floats
        float_cols = df.select_dtypes(include=['float64']).columns
        for col in float_cols:
            df[col] = pd.to_numeric(df[col], downcast='float')
        
        # Convert low-cardinality objects to category
        object_cols = df.select_dtypes(include=['object']).columns
        for col in object_cols:
            if df[col].nunique() / len(df) < 0.5:  # Less than 50% unique values
                df[col] = df[col].astype('category')
        
        optimized_memory = df.memory_usage(deep=True).sum() / 1024**2
        logger.info(f"Memory optimized: {original_memory:.2f} MB → {optimized_memory:.2f} MB "
                   f"({(1 - optimized_memory/original_memory)*100:.1f}% reduction)")
        
        return df
    
    def get_data_summary(self, df: pd.DataFrame) -> Dict:
        """
        Generate comprehensive data summary statistics.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Dictionary with summary statistics
        """
        summary = {
            'n_rows': len(df),
            'n_columns': len(df.columns),
            'memory_mb': df.memory_usage(deep=True).sum() / 1024**2,
            'missing_values': df.isnull().sum().to_dict(),
            'dtypes': df.dtypes.astype(str).to_dict(),
        }
        
        if 'TARGET' in df.columns:
            summary['target_distribution'] = df['TARGET'].value_counts(normalize=True).to_dict()
            summary['default_rate'] = df['TARGET'].mean()
        
        return summary


class DataPreprocessor:
    """
    Handles data cleaning and preprocessing for credit risk modeling.
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize preprocessor with configuration."""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean dataset by handling anomalies and invalid values.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Cleaned DataFrame
        """
        logger.info("Cleaning data...")
        df_clean = df.copy()
        
        # Handle known anomalies in Home Credit dataset
        # DAYS_EMPLOYED: 365243 is anomalous value (XNA in source)
        if 'DAYS_EMPLOYED' in df_clean.columns:
            df_clean['DAYS_EMPLOYED'].replace(365243, None, inplace=True)
            logger.info("Replaced anomalous DAYS_EMPLOYED values")
        
        # Remove rows with all missing values
        n_before = len(df_clean)
        df_clean.dropna(how='all', inplace=True)
        n_after = len(df_clean)
        if n_before != n_after:
            logger.info(f"Removed {n_before - n_after} rows with all missing values")
        
        # Create age from DAYS_BIRTH (negative days)
        if 'DAYS_BIRTH' in df_clean.columns:
            df_clean['AGE'] = (-df_clean['DAYS_BIRTH'] / 365).round(1)
            df_clean['AGE_GROUP'] = pd.cut(
                df_clean['AGE'], 
                bins=[0, 25, 35, 45, 55, 65, 100],
                labels=['18-25', '26-35', '36-45', '46-55', '56-65', '65+']
            )
        
        # Cap extreme outliers (above 99.9th percentile)
        numeric_cols = df_clean.select_dtypes(include=['number']).columns
        for col in numeric_cols:
            if col not in ['TARGET', 'SK_ID_CURR']:
                upper_limit = df_clean[col].quantile(0.999)
                lower_limit = df_clean[col].quantile(0.001)
                df_clean[col] = df_clean[col].clip(lower=lower_limit, upper=upper_limit)
        
        logger.info(f"Data cleaning complete. Shape: {df_clean.shape}")
        return df_clean
    
    def handle_missing_values(self, df: pd.DataFrame, strategy: Optional[Dict] = None) -> pd.DataFrame:
        """
        Handle missing values using configurable strategies.
        
        Args:
            df: Input DataFrame
            strategy: Dictionary mapping column types to imputation strategies
            
        Returns:
            DataFrame with imputed values
        """
        if strategy is None:
            strategy = {
                'numeric': self.config['feature_engineering']['numeric_impute_strategy'],
                'categorical': self.config['feature_engineering']['categorical_impute_strategy']
            }
        
        logger.info("Handling missing values...")
        df_imputed = df.copy()
        
        # Get missing value statistics
        missing_pct = (df_imputed.isnull().sum() / len(df_imputed) * 100).sort_values(ascending=False)
        high_missing = missing_pct[missing_pct > 50]
        if len(high_missing) > 0:
            logger.warning(f"{len(high_missing)} columns have >50% missing values")
        
        # Handle numeric columns
        numeric_cols = df_imputed.select_dtypes(include=['number']).columns
        for col in numeric_cols:
            if col not in ['TARGET', 'SK_ID_CURR'] and df_imputed[col].isnull().any():
                if strategy['numeric'] == 'median':
                    fill_value = df_imputed[col].median()
                elif strategy['numeric'] == 'mean':
                    fill_value = df_imputed[col].mean()
                else:
                    fill_value = 0
                
                df_imputed[col].fillna(fill_value, inplace=True)
        
        # Handle categorical columns
        categorical_cols = df_imputed.select_dtypes(include=['object', 'category']).columns
        for col in categorical_cols:
            if df_imputed[col].isnull().any():
                if strategy['categorical'] == 'mode':
                    fill_value = df_imputed[col].mode()[0] if not df_imputed[col].mode().empty else 'Unknown'
                else:
                    fill_value = 'Unknown'
                
                df_imputed[col].fillna(fill_value, inplace=True)
        
        logger.info("Missing value imputation complete")
        return df_imputed
    
    def remove_duplicates(self, df: pd.DataFrame, subset: Optional[list] = None) -> pd.DataFrame:
        """
        Remove duplicate records.
        
        Args:
            df: Input DataFrame
            subset: Columns to check for duplicates (default: SK_ID_CURR)
            
        Returns:
            DataFrame without duplicates
        """
        if subset is None:
            subset = ['SK_ID_CURR'] if 'SK_ID_CURR' in df.columns else None
        
        n_before = len(df)
        df_dedup = df.drop_duplicates(subset=subset, keep='first')
        n_after = len(df_dedup)
        
        if n_before != n_after:
            logger.info(f"Removed {n_before - n_after} duplicate records")
        
        return df_dedup


if __name__ == "__main__":
    # Example usage
    loader = DataLoader()
    
    # Load training data
    df_train = loader.load_application_train()
    
    # Get summary
    summary = loader.get_data_summary(df_train)
    print(f"\nDataset Summary:")
    print(f"Rows: {summary['n_rows']:,}")
    print(f"Columns: {summary['n_columns']}")
    print(f"Default Rate: {summary.get('default_rate', 0):.2%}")
    
    # Preprocess
    preprocessor = DataPreprocessor()
    df_clean = preprocessor.clean_data(df_train)
    df_processed = preprocessor.handle_missing_values(df_clean)
    
    print(f"\nProcessed shape: {df_processed.shape}")
