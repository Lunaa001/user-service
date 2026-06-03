"""Pydantic request/response schemas"""

from typing import Optional
from pydantic import BaseModel, Field, EmailStr


class RegisterRequest(BaseModel):
    """User registration request schema"""
    email: EmailStr = Field(..., description="User email")
    first_name: str = Field(..., min_length=1, max_length=50, description="First name")
    last_name: str = Field(..., min_length=1, max_length=50, description="Last name")
    password: str = Field(..., min_length=8, max_length=100, description="Password")


class LoginRequest(BaseModel):
    """User login request schema"""
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="User password")


class UpdateUserRequest(BaseModel):
    """Update user request schema"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[EmailStr] = Field(None)


class UserSchema(BaseModel):
    """User response schema"""
    id: int = Field(..., description="User ID")
    email: str = Field(..., description="Email")
    first_name: str = Field(..., alias="firstName", description="First name")
    last_name: str = Field(..., alias="lastName", description="Last name")
    created_at: str = Field(..., alias="createdAt", description="Creation timestamp")
    updated_at: str = Field(default="", description="Update timestamp")
    
    class Config:
        from_attributes = True
        populate_by_name = True


class TokenSchema(BaseModel):
    """Token response schema"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer")
    user: UserSchema = Field(..., description="User data")


class HealthSchema(BaseModel):
    """Health check response schema"""
    status: str = Field(...)
    service: str = Field(...)
    version: str = Field(...)
