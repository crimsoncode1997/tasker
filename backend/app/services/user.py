"""
User service for business logic.
"""
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import structlog

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password

logger = structlog.get_logger()


class UserService:
    """User service class."""
    
    async def get_by_id(self, db: AsyncSession, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email."""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    async def create(self, db: AsyncSession, user_in: UserCreate) -> User:
        """Create a new user."""
        # Check if user already exists
        existing_user = await self.get_by_email(db, user_in.email)
        if existing_user:
            raise ValueError("User with this email already exists")
        
        # Create user
        hashed_password = get_password_hash(user_in.password)
        user = User(
            email=user_in.email,
            full_name=user_in.full_name,
            hashed_password=hashed_password,
            is_active=user_in.is_active,
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        logger.info("User created", user_id=str(user.id), email=user.email)
        return user
    
    async def update(self, db: AsyncSession, user: User, user_in: UserUpdate) -> User:
        """Update user."""
        update_data = user_in.model_dump(exclude_unset=True)
        
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
        
        for field, value in update_data.items():
            setattr(user, field, value)
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        logger.info("User updated", user_id=str(user.id))
        return user
    
    async def authenticate(self, db: AsyncSession, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password."""
        user = await self.get_by_email(db, email)
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        if not user.is_active:
            return None
        
        return user


# Create service instance
user_service = UserService()

