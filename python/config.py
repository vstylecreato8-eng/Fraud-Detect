"""
Configuration settings for the Flask application
"""
import os
from datetime import timedelta

class Config:
    """Base configuration"""
    # Flask settings
    DEBUG = False
    TESTING = False
    
    # CORS settings
    CORS_ORIGINS = ["http://localhost:5173", "http://localhost:3000"]
    
    # Model settings - use absolute path
    _script_dir = os.path.dirname(os.path.abspath(__file__))
    MODEL_PATH = os.getenv('MODEL_PATH', os.path.join(_script_dir, 'trained_model.pkl'))
    
    # API settings
    API_TIMEOUT = 30
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max request size
    
    # Logging settings
    LOG_LEVEL = 'INFO'


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    CORS_ORIGINS = ["*"]


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    MODEL_PATH = 'test_model.pkl'


# Get config from environment
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
