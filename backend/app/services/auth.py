# from sqlalchemy.ext.asyncio import AsyncSession
# from app.core.security import verify_password
# from app.models.user import User
# from app.core.database import get_user_by_email

# class AuthService:
#     async def authenticate_user(self, db: AsyncSession, email: str, password: str) -> User | None:
#         user = await get_user_by_email(db, email)
#         if not user or not verify_password(password, user.hashed_password):
#             return None
#         return user

#     async def get_current_user_from_token(self, token: str, db: AsyncSession) -> User | None:
#         # JWT decode stub
#         return None

# auth_service = AuthService()
