"""Authentication service - handles user registration, login, and JWT"""

from datetime import timedelta
from typing import Optional, Dict, Any
import logging

from app.security.jwt_handler import JWTHandler
from app.clients.persistence_client import persistence_client

logger = logging.getLogger(__name__)


class AuthService:
    """Business logic for authentication"""
    
    @staticmethod
    async def register(
        email: str,
        first_name: str,
        last_name: str,
        password: str
    ) -> Optional[Dict[str, Any]]:
        """
        Register a new user
        
        Workflow:
        1. Hash password
        2. Call Persistence Service to create user
        3. Generate JWT token
        4. Return user + token
        
        Args:
            email: User email
            first_name: User first name
            last_name: User last name
            password: Plain password
            
        Returns:
            Dictionary with user data and access token, or None if failed
        """
        try:
            # Check if user already exists
            existing_user = await persistence_client.get_user_by_email(email)
            if existing_user:
                logger.warning(f"User with email {email} already exists")
                return None
            
            # Hash password
            password_hash = JWTHandler.hash_password(password)
            
            # Create user in Persistence Service
            user = await persistence_client.create_user(
                email=email,
                first_name=first_name,
                last_name=last_name,
                password_hash=password_hash
            )
            
            if not user:
                logger.error("Failed to create user in Persistence Service")
                return None
            
            # Generate JWT token
            access_token = JWTHandler.create_access_token(
                data={"sub": user["id"], "email": user["email"]}
            )
            
            return {
                "user": user,
                "access_token": access_token,
                "token_type": "bearer"
            }
            
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            return None
    
    @staticmethod
    async def login(email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate user and return JWT token
        
        Workflow:
        1. Get user from Persistence Service by email
        2. Verify password
        3. Generate JWT token
        4. Return token
        
        Args:
            email: User email
            password: Plain password
            
        Returns:
            Dictionary with access token and user data, or None if failed
        """
        try:
            # Get user from Persistence Service
            user = await persistence_client.get_user_by_email(email)
            
            if not user:
                logger.warning(f"Login attempt for non-existent user: {email}")
                return None
            
            # Verify password
            if not JWTHandler.verify_password(password, user.get("passwordHash", "")):
                logger.warning(f"Invalid password for user: {email}")
                return None
            
            # Generate JWT token
            access_token = JWTHandler.create_access_token(
                data={"sub": user["id"], "email": user["email"]}
            )
            
            return {
                "user": user,
                "access_token": access_token,
                "token_type": "bearer"
            }
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return None
    
    @staticmethod
    async def validate_token(token: str) -> Optional[Dict[str, Any]]:
        """
        Validate JWT token and return payload
        
        Args:
            token: JWT token string
            
        Returns:
            Token payload or None if invalid
        """
        return JWTHandler.verify_token(token)
    
    @staticmethod
    async def get_current_user(token: str) -> Optional[Dict[str, Any]]:
        """
        Get current user from JWT token
        
        Args:
            token: JWT token string
            
        Returns:
            User data from Persistence Service or None
        """
        payload = JWTHandler.verify_token(token)
        
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        # Get user from Persistence Service
        user = await persistence_client.get_user(user_id)
        return user
