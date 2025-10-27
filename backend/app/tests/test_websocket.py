"""
Tests for WebSocket functionality and board collaboration.
"""
import pytest
import json
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.core.redis import redis_manager
from app.models.user import User
from app.models.board import Board, BoardMember
from app.core.security import create_access_token


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
async def test_user(db: AsyncSession):
    """Create a test user."""
    user = User(
        email="test@example.com",
        hashed_password="hashed_password",
        full_name="Test User",
        is_active=True
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
async def test_board(db: AsyncSession, test_user: User):
    """Create a test board."""
    board = Board(
        title="Test Board",
        description="Test Description",
        owner_id=test_user.id
    )
    db.add(board)
    await db.commit()
    await db.refresh(board)
    
    # Add owner as member
    member = BoardMember(
        board_id=board.id,
        user_id=test_user.id,
        role="owner"
    )
    db.add(member)
    await db.commit()
    
    return board


@pytest.fixture
async def another_user(db: AsyncSession):
    """Create another test user."""
    user = User(
        email="another@example.com",
        hashed_password="hashed_password",
        full_name="Another User",
        is_active=True
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


class TestWebSocketConnection:
    """Test WebSocket connection functionality."""
    
    @pytest.mark.asyncio
    async def test_websocket_connection_without_token(self, client: TestClient, test_board: Board):
        """Test WebSocket connection without token fails."""
        with client.websocket_connect(f"/api/v1/ws/board/{test_board.id}") as websocket:
            # Should close with error code
            assert websocket.close_code == 4001
    
    @pytest.mark.asyncio
    async def test_websocket_connection_with_invalid_token(self, client: TestClient, test_board: Board):
        """Test WebSocket connection with invalid token fails."""
        with client.websocket_connect(f"/api/v1/ws/board/{test_board.id}?token=invalid_token") as websocket:
            # Should close with error code
            assert websocket.close_code == 4001
    
    @pytest.mark.asyncio
    async def test_websocket_connection_with_valid_token(self, client: TestClient, test_user: User, test_board: Board):
        """Test WebSocket connection with valid token succeeds."""
        token = create_access_token(str(test_user.id))
        
        with client.websocket_connect(f"/api/v1/ws/board/{test_board.id}?token={token}") as websocket:
            # Should receive welcome message
            data = websocket.receive_text()
            message = json.loads(data)
            assert message["type"] == "connection"
            assert message["user_id"] == str(test_user.id)
    
    @pytest.mark.asyncio
    async def test_websocket_connection_access_denied(self, client: TestClient, another_user: User, test_board: Board):
        """Test WebSocket connection without board access fails."""
        token = create_access_token(str(another_user.id))
        
        with client.websocket_connect(f"/api/v1/ws/board/{test_board.id}?token={token}") as websocket:
            # Should close with access denied code
            assert websocket.close_code == 4003


class TestWebSocketMessageHandling:
    """Test WebSocket message handling."""
    
    @pytest.mark.asyncio
    async def test_card_move_message(self, client: TestClient, test_user: User, test_board: Board):
        """Test card move message handling."""
        token = create_access_token(str(test_user.id))
        
        with patch('app.api.v1.endpoints.websocket.card_service') as mock_card_service:
            mock_card_service.move_card = AsyncMock()
            mock_card_service.move_card.return_value = AsyncMock()
            mock_card_service.move_card.return_value.updated_at.isoformat.return_value = "2023-01-01T00:00:00"
            
            with client.websocket_connect(f"/api/v1/ws/board/{test_board.id}?token={token}") as websocket:
                # Send card move message
                message = {
                    "type": "card_move",
                    "card_id": "test-card-id",
                    "new_list_id": "test-list-id",
                    "new_position": 1
                }
                websocket.send_text(json.dumps(message))
                
                # Should not raise any errors
                # In a real test, you'd verify the card was moved in the database
    
    @pytest.mark.asyncio
    async def test_invalid_message_format(self, client: TestClient, test_user: User, test_board: Board):
        """Test handling of invalid message format."""
        token = create_access_token(str(test_user.id))
        
        with client.websocket_connect(f"/api/v1/ws/board/{test_board.id}?token={token}") as websocket:
            # Send invalid JSON
            websocket.send_text("invalid json")
            
            # Should receive error message
            data = websocket.receive_text()
            message = json.loads(data)
            assert message["type"] == "error"
            assert "Invalid JSON format" in message["message"]


class TestBoardInvitation:
    """Test board invitation functionality."""
    
    @pytest.mark.asyncio
    async def test_invite_user_to_board(self, client: TestClient, test_user: User, test_board: Board, another_user: User):
        """Test inviting a user to a board."""
        token = create_access_token(str(test_user.id))
        
        headers = {"Authorization": f"Bearer {token}"}
        data = {
            "email": another_user.email,
            "role": "member"
        }
        
        response = client.post(f"/api/v1/boards/{test_board.id}/invite", json=data, headers=headers)
        assert response.status_code == 200
        
        # Verify user was added as member
        response = client.get(f"/api/v1/boards/{test_board.id}", headers=headers)
        assert response.status_code == 200
        board_data = response.json()
        
        # Check if the invited user is in the members list
        member_emails = [member["user"]["email"] for member in board_data["members"]]
        assert another_user.email in member_emails
    
    @pytest.mark.asyncio
    async def test_invite_nonexistent_user(self, client: TestClient, test_user: User, test_board: Board):
        """Test inviting a non-existent user fails."""
        token = create_access_token(str(test_user.id))
        
        headers = {"Authorization": f"Bearer {token}"}
        data = {
            "email": "nonexistent@example.com",
            "role": "member"
        }
        
        response = client.post(f"/api/v1/boards/{test_board.id}/invite", json=data, headers=headers)
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_invite_existing_member(self, client: TestClient, test_user: User, test_board: Board):
        """Test inviting an existing member fails."""
        token = create_access_token(str(test_user.id))
        
        headers = {"Authorization": f"Bearer {token}"}
        data = {
            "email": test_user.email,  # Owner is already a member
            "role": "member"
        }
        
        response = client.post(f"/api/v1/boards/{test_board.id}/invite", json=data, headers=headers)
        assert response.status_code == 400
        assert "already a member" in response.json()["detail"]


class TestRedisIntegration:
    """Test Redis integration for real-time updates."""
    
    @pytest.mark.asyncio
    async def test_redis_connection(self):
        """Test Redis connection."""
        # This test would require Redis to be running
        # In a real test environment, you'd use a test Redis instance
        pass
    
    @pytest.mark.asyncio
    async def test_board_update_broadcast(self, test_board: Board):
        """Test broadcasting board updates via Redis."""
        # Mock Redis operations
        with patch('app.core.redis.redis_manager.redis') as mock_redis:
            mock_redis.publish = AsyncMock()
            
            message = {
                "type": "card_moved",
                "card_id": "test-card",
                "user_id": "test-user"
            }
            
            await redis_manager.publish_board_update(str(test_board.id), message)
            
            # Verify Redis publish was called
            mock_redis.publish.assert_called_once()
            call_args = mock_redis.publish.call_args
            assert call_args[0][0] == f"board:{test_board.id}"
            assert json.loads(call_args[0][1]) == message


@pytest.mark.asyncio
async def test_board_member_permissions(db: AsyncSession, test_user: User, another_user: User, test_board: Board):
    """Test board member permissions."""
    from app.services.board import board_service
    
    # Test owner has access
    has_access = await board_service.check_user_access(db, test_board.id, test_user.id)
    assert has_access is True
    
    # Test non-member has no access
    has_access = await board_service.check_user_access(db, test_board.id, another_user.id)
    assert has_access is False
    
    # Test owner role
    role = await board_service.get_user_role(db, test_board.id, test_user.id)
    assert role == "owner"
    
    # Test non-member role
    role = await board_service.get_user_role(db, test_board.id, another_user.id)
    assert role is None


@pytest.mark.asyncio
async def test_board_member_invitation_flow(db: AsyncSession, test_user: User, another_user: User, test_board: Board):
    """Test complete board invitation flow."""
    from app.services.board import board_service
    
    # Invite user
    await board_service.invite_user(db, test_board.id, another_user.email, "member")
    
    # Verify user now has access
    has_access = await board_service.check_user_access(db, test_board.id, another_user.id)
    assert has_access is True
    
    # Verify user role
    role = await board_service.get_user_role(db, test_board.id, another_user.id)
    assert role == "member"
