"""
Seed database with sample data.
"""
import asyncio
import uuid
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.board import Board, BoardMember
from app.models.list import List as ListModel
from app.models.card import Card
from app.core.security import get_password_hash


async def create_sample_data():
    """Create sample data for development."""
    async with AsyncSessionLocal() as db:
        # Create sample user
        user = User(
            id=uuid.uuid4(),
            email="demo@tasker.com",
            full_name="Demo User",
            hashed_password=get_password_hash("demo123"),
            is_active=True,
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        print(f"Created user: {user.email}")
        
        # Create sample board
        board = Board(
            id=uuid.uuid4(),
            title="Sample Project Board",
            description="A sample board to demonstrate Tasker functionality",
            owner_id=user.id,
        )
        
        db.add(board)
        await db.commit()
        await db.refresh(board)
        
        print(f"Created board: {board.title}")
        
        # Add user as board member
        member = BoardMember(
            board_id=board.id,
            user_id=user.id,
            role="owner"
        )
        db.add(member)
        
        # Create sample lists
        lists_data = [
            {"title": "To Do", "position": 1.0},
            {"title": "In Progress", "position": 2.0},
            {"title": "Done", "position": 3.0},
        ]
        
        created_lists = []
        for list_data in lists_data:
            list_obj = ListModel(
                title=list_data["title"],
                board_id=board.id,
                position=list_data["position"],
            )
            db.add(list_obj)
            created_lists.append(list_obj)
        
        await db.commit()
        
        for list_obj in created_lists:
            await db.refresh(list_obj)
            print(f"Created list: {list_obj.title}")
        
        # Create sample cards
        cards_data = [
            {
                "title": "Setup project environment",
                "description": "Install dependencies and configure development environment",
                "list_id": created_lists[0].id,
                "position": 1.0,
                "due_date": date.today() + timedelta(days=1),
            },
            {
                "title": "Design database schema",
                "description": "Create database models and relationships",
                "list_id": created_lists[0].id,
                "position": 2.0,
                "due_date": date.today() + timedelta(days=2),
            },
            {
                "title": "Implement authentication",
                "description": "Add user registration and login functionality",
                "list_id": created_lists[1].id,
                "position": 1.0,
                "assignee_id": user.id,
                "due_date": date.today() + timedelta(days=3),
            },
            {
                "title": "Create API endpoints",
                "description": "Implement CRUD operations for boards, lists, and cards",
                "list_id": created_lists[1].id,
                "position": 2.0,
                "assignee_id": user.id,
                "due_date": date.today() + timedelta(days=4),
            },
            {
                "title": "Setup frontend",
                "description": "Create React components and routing",
                "list_id": created_lists[2].id,
                "position": 1.0,
                "due_date": date.today() - timedelta(days=1),
            },
            {
                "title": "Add drag and drop",
                "description": "Implement drag and drop functionality for cards",
                "list_id": created_lists[2].id,
                "position": 2.0,
                "due_date": date.today() - timedelta(days=2),
            },
        ]
        
        for card_data in cards_data:
            card = Card(**card_data)
            db.add(card)
        
        await db.commit()
        
        print("Created sample cards")
        print("\nSample data created successfully!")
        print(f"Login with: demo@tasker.com / demo123")


if __name__ == "__main__":
    asyncio.run(create_sample_data())
