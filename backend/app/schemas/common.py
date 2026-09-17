from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class ApiResponse(BaseModel):
    success: bool = True
    message: str = "Operation successful"
    data: Optional[Any] = None

class Coordinates(BaseModel):
    latitude: float
    longitude: float
    accuracy: Optional[float] = None
