import os

try:
    from pydantic_settings import BaseSettings
except ImportError:
    try:
        from pydantic import BaseSettings
    except ImportError:
        BaseSettings = object

class Settings:
    PROJECT_NAME: str = "SAMANVAY AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "raahat-super-secret-key-production-disaster-response-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./raahat.db")
    
    # Need Score Weights (Sum = 1.0)
    WEIGHT_MEDICAL_SEVERITY: float = 0.30
    WEIGHT_PEOPLE_AFFECTED: float = 0.25
    WEIGHT_UNMET_DEMAND: float = 0.20
    WEIGHT_ACCESSIBILITY: float = 0.15
    WEIGHT_VULNERABILITY: float = 0.10
    
    # Duplicate SOS / Clustering
    SOS_CLUSTER_DISTANCE_METERS: float = 150.0  # 150 meters
    SOS_CLUSTER_TIME_WINDOW_SECONDS: int = 180   # 3 minutes
    
    # Stale Resource Heartbeat
    RESOURCE_HEARTBEAT_TIMEOUT_SECONDS: int = 120 # 2 minutes
    
    # Default Base Region (Pune City coordinates for demo)
    BASE_LATITUDE: float = 18.5204
    BASE_LONGITUDE: float = 73.8567

settings = Settings()
