"""Pydantic models for database entities"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class UserBase(BaseModel):
    """Base user model"""
    email: str = Field(..., description="User email address")
    first_name: str = Field(..., description="User first name")
    last_name: str = Field(..., description="User last name")


class UserCreate(UserBase):
    """User creation model"""
    password: str = Field(..., min_length=8, description="User password (min 8 chars)")


class UserLogin(BaseModel):
    """User login model"""
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class UserUpdate(BaseModel):
    """User update model"""
    first_name: Optional[str] = Field(None, description="User first name")
    last_name: Optional[str] = Field(None, description="User last name")
    email: Optional[str] = Field(None, description="User email address")


class UserResponse(UserBase):
    """User response model"""
    id: int = Field(..., description="User ID")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user: UserResponse = Field(..., description="User information")


class Token(BaseModel):
    """JWT token payload"""
    access_token: str = Field(..., description="JWT token")
    token_type: str = Field(default="bearer", description="Token type")
