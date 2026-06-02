"""Authentication API endpoints"""

from fastapi import APIRouter, HTTPException, Depends, Header, status
from typing import Optional
import logging

from app.schemas import RegisterRequest, LoginRequest, UserSchema, TokenSchema
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=TokenSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new user account and return JWT token"
)
async def register(request: RegisterRequest):
    """
    Register a new user
    
    Returns JWT access token and user information
    """
    try:
        result = await AuthService.register(
            email=request.email,
            first_name=request.first_name,
            last_name=request.last_name,
            password=request.password
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already exists or registration failed"
            )
        
        return {
            "access_token": result["access_token"],
            "token_type": result["token_type"],
            "user": result["user"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post(
    "/login",
    response_model=TokenSchema,
    status_code=status.HTTP_200_OK,
    summary="Login user",
    description="Authenticate user and return JWT token"
)
async def login(request: LoginRequest):
    """
    Login user with email and password
    
    Returns JWT access token and user information
    """
    try:
        result = await AuthService.login(
            email=request.email,
            password=request.password
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        return {
            "access_token": result["access_token"],
            "token_type": result["token_type"],
            "user": result["user"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.get(
    "/me",
    response_model=UserSchema,
    status_code=status.HTTP_200_OK,
    summary="Get current user",
    description="Get current authenticated user information"
)
async def get_current_user(authorization: Optional[str] = Header(None)):
    """
    Get current user from JWT token
    
    Requires Authorization header: Bearer <token>
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )
    
    try:
        # Extract token from "Bearer <token>"
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format"
            )
        
        token = parts[1]
        user = await AuthService.get_current_user(token)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get current user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get current user"
        )
