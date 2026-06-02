"""HTTP Client for Persistence Service communication"""

import httpx
from typing import Optional, Dict, Any
import logging

from app.config.settings import settings

logger = logging.getLogger(__name__)


class PersistenceServiceClient:
    """Client for communicating with Persistence Service (Java backend)"""
    
    def __init__(self):
        self.base_url = settings.persistence_service_url
        self.timeout = settings.request_timeout
    
    async def create_user(
        self,
        email: str,
        first_name: str,
        last_name: str,
        password_hash: str
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new user in Persistence Service
        
        Args:
            email: User email
            first_name: User first name
            last_name: User last name
            password_hash: Hashed password
            
        Returns:
            User data dict or None if failed
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/users",
                    json={
                        "email": email,
                        "firstName": first_name,
                        "lastName": last_name,
                        "passwordHash": password_hash,
                    }
                )
                
                if response.status_code == 201:
                    return response.json()
                else:
                    logger.error(f"Failed to create user: {response.status_code}")
                    return None
                    
        except httpx.TimeoutException:
            logger.error("Timeout connecting to Persistence Service")
            return None
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return None
    
    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user by ID from Persistence Service
        
        Args:
            user_id: User ID
            
        Returns:
            User data dict or None if not found
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/users/{user_id}"
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"User {user_id} not found")
                    return None
                    
        except httpx.TimeoutException:
            logger.error("Timeout connecting to Persistence Service")
            return None
        except Exception as e:
            logger.error(f"Error getting user: {str(e)}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get user by email from Persistence Service
        
        Args:
            email: User email
            
        Returns:
            User data dict or None if not found
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/users/email/{email}"
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    logger.info(f"User with email {email} not found")
                    return None
                else:
                    logger.error(f"Error getting user by email: {response.status_code}")
                    return None
                    
        except httpx.TimeoutException:
            logger.error("Timeout connecting to Persistence Service")
            return None
        except Exception as e:
            logger.error(f"Error getting user by email: {str(e)}")
            return None
    
    async def update_user(
        self,
        user_id: int,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update user in Persistence Service
        
        Args:
            user_id: User ID
            first_name: Updated first name
            last_name: Updated last name
            email: Updated email
            
        Returns:
            Updated user data or None if failed
        """
        try:
            update_data = {}
            if first_name:
                update_data["firstName"] = first_name
            if last_name:
                update_data["lastName"] = last_name
            if email:
                update_data["email"] = email
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.put(
                    f"{self.base_url}/api/v1/users/{user_id}",
                    json=update_data
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Failed to update user: {response.status_code}")
                    return None
                    
        except httpx.TimeoutException:
            logger.error("Timeout connecting to Persistence Service")
            return None
        except Exception as e:
            logger.error(f"Error updating user: {str(e)}")
            return None


# Global client instance
persistence_client = PersistenceServiceClient()
