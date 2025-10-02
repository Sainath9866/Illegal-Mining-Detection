"""
Configuration file for Illegal Mining Detection System
"""

import os
from typing import Dict, Any

class Config:
    """Configuration class for the mining detection system"""
    
    # API Configuration
    API_HOST = "0.0.0.0"
    API_PORT = 8000
    API_TITLE = "Illegal Mining Detection API"
    API_VERSION = "1.0.0"
    
    # Data Configuration
    DEFAULT_OUTPUT_DIR = "output"
    UPLOADS_DIR = "uploads"
    STATIC_DIR = "static"
    
    # Google Earth Engine Configuration
    GEE_SERVICE_ACCOUNT_PATH = os.getenv("GEE_SERVICE_ACCOUNT_PATH", None)
    GEE_PROJECT = os.getenv("GEE_PROJECT", "your-gee-project")
    
    # Analysis Configuration
    DEFAULT_NDVI_THRESHOLD = 0.2
    DEFAULT_BSI_THRESHOLD = 0.3
    DEFAULT_MIN_AREA_M2 = 1000.0
    DEFAULT_PIXEL_SIZE = 10.0
    DEFAULT_REFERENCE_BUFFER = 100.0
    
    # Visualization Configuration
    DEFAULT_MAP_CENTER = (28.0, 77.0)  # Default center for India
    DEFAULT_ZOOM_START = 12
    
    # Report Configuration
    REPORT_TITLE = "Illegal Mining Detection Report"
    COMPANY_NAME = "Smart India Hackathon Team"
    
    # Logging Configuration
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """Get all configuration as dictionary"""
        return {
            "api": {
                "host": cls.API_HOST,
                "port": cls.API_PORT,
                "title": cls.API_TITLE,
                "version": cls.API_VERSION
            },
            "data": {
                "output_dir": cls.DEFAULT_OUTPUT_DIR,
                "uploads_dir": cls.UPLOADS_DIR,
                "static_dir": cls.STATIC_DIR
            },
            "gee": {
                "service_account_path": cls.GEE_SERVICE_ACCOUNT_PATH,
                "project": cls.GEE_PROJECT
            },
            "analysis": {
                "ndvi_threshold": cls.DEFAULT_NDVI_THRESHOLD,
                "bsi_threshold": cls.DEFAULT_BSI_THRESHOLD,
                "min_area_m2": cls.DEFAULT_MIN_AREA_M2,
                "pixel_size": cls.DEFAULT_PIXEL_SIZE,
                "reference_buffer": cls.DEFAULT_REFERENCE_BUFFER
            },
            "visualization": {
                "map_center": cls.DEFAULT_MAP_CENTER,
                "zoom_start": cls.DEFAULT_ZOOM_START
            },
            "report": {
                "title": cls.REPORT_TITLE,
                "company_name": cls.COMPANY_NAME
            },
            "logging": {
                "level": cls.LOG_LEVEL,
                "format": cls.LOG_FORMAT
            }
        }
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate configuration"""
        try:
            # Check if required directories exist or can be created
            os.makedirs(cls.DEFAULT_OUTPUT_DIR, exist_ok=True)
            os.makedirs(cls.UPLOADS_DIR, exist_ok=True)
            os.makedirs(cls.STATIC_DIR, exist_ok=True)
            
            # Validate thresholds
            assert 0 <= cls.DEFAULT_NDVI_THRESHOLD <= 1, "NDVI threshold must be between 0 and 1"
            assert 0 <= cls.DEFAULT_BSI_THRESHOLD <= 1, "BSI threshold must be between 0 and 1"
            assert cls.DEFAULT_MIN_AREA_M2 > 0, "Minimum area must be positive"
            assert cls.DEFAULT_PIXEL_SIZE > 0, "Pixel size must be positive"
            assert cls.DEFAULT_REFERENCE_BUFFER > 0, "Reference buffer must be positive"
            
            return True
            
        except Exception as e:
            print(f"Configuration validation failed: {e}")
            return False

# Environment-specific configurations
class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    LOG_LEVEL = "DEBUG"

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    LOG_LEVEL = "WARNING"

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    LOG_LEVEL = "DEBUG"
    DEFAULT_OUTPUT_DIR = "test_output"

# Configuration mapping
config_mapping = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig
}

def get_config(env: str = "development") -> Config:
    """Get configuration for specific environment"""
    return config_mapping.get(env, DevelopmentConfig)
