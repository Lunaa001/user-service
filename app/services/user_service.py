"""User service - handles user operations"""

from typing import Optional, Dict, Any
import logging

from app.clients.persistence_client import persistence_client

logger = logging.getLogger(__name__)


class UserService:
    """Business logic for user management"""
    
    @staticmethod
    async def get_user(user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user by ID
        
        Args:
            user_id: User ID
            
        Returns:
            User data or None if not found
        """
        try:
            user = await persistence_client.get_user(user_id)
            return user
        except Exception as e:
            logger.error(f"Error getting user: {str(e)}")
            return None
    
    @staticmethod
    async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        """
        Get user by email
        
        Args:
            email: User email
            
        Returns:
            User data or None if not found
        """
        try:
            user = await persistence_client.get_user_by_email(email)
            return user
        except Exception as e:
            logger.error(f"Error getting user by email: {str(e)}")
            return None
    
    @staticmethod
    async def update_user(
        user_id: int,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update user information
        
        Args:
            user_id: User ID
            first_name: New first name
            last_name: New last name
            email: New email
            
        Returns:
            Updated user data or None if failed
        """
        try:
            user = await persistence_client.update_user(
                user_id=user_id,
                first_name=first_name,
                last_name=last_name,
                email=email
            )
            return user
        except Exception as e:
            logger.error(f"Error updating user: {str(e)}")
            return None

    @staticmethod
    def validate_user_data(data: Optional[Dict[str, Any]]) -> Dict[str, str]:
        """Validate user input data."""
        if not data or not isinstance(data, dict):
            raise ValidationError("Request body must be valid JSON")

        email = data.get("email", "").strip()
        nombre = data.get("nombre", "").strip()

        if not email:
            raise ValidationError("Email is required")

        if not nombre:
            raise ValidationError("Name (nombre) is required")

        # RFC 5322 simplified email validation pattern
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValidationError("Email format is invalid")

        # Validate nombre length (reasonable bounds)
        if len(nombre) > 255:
            raise ValidationError("Name (nombre) must not exceed 255 characters")

        if len(nombre) < 2:
            raise ValidationError("Name (nombre) must be at least 2 characters")

        return {"email": email, "nombre": nombre}

    @staticmethod
    def create_user(email: str, nombre: str) -> Dict[str, Any]:
        """
        Create a new user by delegating to Persistence microservice.
        """
        persistence_url = current_app.config.get("PERSISTENCE_URL")
        
        try:
            response = requests.post(
                f"{persistence_url}/api/v1/db/users",
                json={"email": email, "nombre": nombre},
                timeout=5
            )
            
            if response.status_code == 409:
                raise ValidationError(f"User with email '{email}' already exists")
            elif response.status_code >= 400:
                error_msg = response.json().get("detail", "Error in persistence service")
                raise UpstreamError(error_msg, response.status_code)
                
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise UpstreamError(f"Failed to connect to persistence service: {str(e)}", 503)

    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a user by delegating to Persistence microservice.
        """
        persistence_url = current_app.config.get("PERSISTENCE_URL")
        
        try:
            response = requests.get(
                f"{persistence_url}/api/v1/db/users/{user_id}",
                timeout=5
            )
            
            if response.status_code == 404:
                return None
            elif response.status_code >= 400:
                error_msg = response.json().get("detail", "Error in persistence service")
                raise UpstreamError(error_msg, response.status_code)
                
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise UpstreamError(f"Failed to connect to persistence service: {str(e)}", 503)
