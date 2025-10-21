"""
Main API router.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, boards, lists, cards, notifications

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(boards.router, prefix="/boards", tags=["boards"])
api_router.include_router(lists.router, prefix="/lists", tags=["lists"])
api_router.include_router(cards.router, prefix="/cards", tags=["cards"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])

