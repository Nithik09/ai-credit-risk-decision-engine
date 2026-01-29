"""
Download Home Credit Default Risk dataset from Kaggle.
"""
import os
import zipfile
from pathlib import Path
from loguru import logger

def download_dataset():
    """Download and extract Home Credit dataset."""
    # Setup paths
    project_root = Path(__file__).parent.parent
    raw_data_path = project_root / "data" / "raw"
    raw_data_path.mkdir(parents=True, exist_ok=True)
    
    logger.info("Starting dataset download from Kaggle...")
    
    try:
        # Import kaggle after checking credentials
        import kaggle
        
        # Download competition files
        competition_name = "home-credit-default-risk"
        logger.info(f"Downloading {competition_name} dataset...")
        
        kaggle.api.competition_download_files(
            competition_name,
            path=str(raw_data_path),
            quiet=False
        )
        
        # Extract zip file
        zip_file = raw_data_path / f"{competition_name}.zip"
        if zip_file.exists():
            logger.info(f"Extracting {zip_file}...")
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(raw_data_path)
            
            logger.info(f"Dataset extracted to {raw_data_path}")
            
            # Remove zip file to save space
            zip_file.unlink()
            logger.info("Removed zip file")
            
            # List downloaded files
            files = list(raw_data_path.glob("*.csv"))
            logger.info(f"Downloaded {len(files)} CSV files:")
            for f in files:
                size_mb = f.stat().st_size / (1024 * 1024)
                logger.info(f"  - {f.name} ({size_mb:.2f} MB)")
            
            logger.success("Dataset download completed successfully!")
            return True
            
        else:
            logger.error(f"Zip file not found: {zip_file}")
            return False
            
    except Exception as e:
        logger.error(f"Error downloading dataset: {e}")
        logger.info("\nPlease ensure:")
        logger.info("1. You have Kaggle API credentials set up")
        logger.info("2. Credentials are at: C:\\Users\\nithi\\.kaggle\\kaggle.json")
        logger.info("3. You have accepted the competition rules at:")
        logger.info("   https://www.kaggle.com/c/home-credit-default-risk/rules")
        return False

if __name__ == "__main__":
    success = download_dataset()
    if not success:
        exit(1)
