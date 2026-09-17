from pydantic import BaseModel
from typing import Optional

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str
    responder_id: Optional[str] = None
    name: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    username: str
    email: Optional[str] = None
    role: str
    is_active: bool
