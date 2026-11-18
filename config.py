import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Base Configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'nigerian-civil-service-secure-key-2026-fgn-ret')
    
    # MySQL Database Configuration
    # Supports DATABASE_URL (e.g. Railway), MYSQL_URL, or discrete credentials (with or without underscores)
    MYSQL_USER = os.environ.get('MYSQL_USER') or os.environ.get('MYSQLUSER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or os.environ.get('MYSQLPASSWORD', '')
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or os.environ.get('MYSQLHOST', 'localhost')
    MYSQL_PORT = os.environ.get('MYSQL_PORT') or os.environ.get('MYSQLPORT', '3306')
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE') or os.environ.get('MYSQLDATABASE', 'retirement_clearance_db')
    
    DATABASE_URL = os.environ.get('DATABASE_URL') or os.environ.get('MYSQL_URL')
    if DATABASE_URL:
        # Normalize postgres/mysql URLs if supplied by cloud providers
        if DATABASE_URL.startswith('mysql://'):
            DATABASE_URL = DATABASE_URL.replace('mysql://', 'mysql+pymysql://', 1)
        elif DATABASE_URL.startswith('postgres://'):
            DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        # Standard local / XAMPP or discrete MySQL connection via PyMySQL
        SQLALCHEMY_DATABASE_URI = (
            f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"
        )
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 280,
        'pool_pre_ping': True,
    }
    
    # Session and Security
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=int(os.environ.get('SESSION_TIMEOUT_MINUTES', 60)))
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    WTF_CSRF_TIME_LIMIT = 3600
    
    # File Uploads
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max request size
    if os.environ.get('VERCEL'):
        UPLOAD_FOLDER = os.path.join('/tmp', 'uploads')
    else:
        UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
    
    # OCR and Biometrics configuration
    TESSERACT_CMD = os.environ.get('TESSERACT_CMD', r'C:\Program Files\Tesseract-OCR\tesseract.exe')
    BIOMETRIC_HARDWARE_ENABLED = os.environ.get('BIOMETRIC_HARDWARE_ENABLED', 'False').lower() in ('true', '1')
    
    # System Metadata
    APP_NAME = "RetireClear"
    APP_SUBTITLE = "National Retirement Clearance Portal"
    COUNTRY = "Public Service"
    CURRENCY = "₦"
    TIMEZONE = "UTC"

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    # Use SQLite memory or isolated test db for fast automated tests
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL', 'sqlite:///:memory:')

class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
