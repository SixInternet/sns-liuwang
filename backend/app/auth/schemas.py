from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    username: str

class UserResponse(BaseModel):
    id: UUID
    username: str
    email: str | None = None
    is_active: bool
    created_at: datetime
