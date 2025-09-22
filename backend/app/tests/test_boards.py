"""
Board tests.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_board(client: AsyncClient):
    """Test creating a board."""
    # Register user and get token
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    
    register_response = await client.post("/api/v1/auth/register", json=user_data)
    tokens = register_response.json()
    
    # Create board
    board_data = {
        "title": "Test Board",
        "description": "A test board"
    }
    
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    response = await client.post("/api/v1/boards", json=board_data, headers=headers)
    
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == board_data["title"]
    assert data["description"] == board_data["description"]
    assert data["owner"]["email"] == user_data["email"]


@pytest.mark.asyncio
async def test_get_boards(client: AsyncClient):
    """Test getting user's boards."""
    # Register user and get token
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    
    register_response = await client.post("/api/v1/auth/register", json=user_data)
    tokens = register_response.json()
    
    # Create a board
    board_data = {"title": "Test Board"}
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    await client.post("/api/v1/boards", json=board_data, headers=headers)
    
    # Get boards
    response = await client.get("/api/v1/boards", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == board_data["title"]


@pytest.mark.asyncio
async def test_get_board_by_id(client: AsyncClient):
    """Test getting a specific board."""
    # Register user and get token
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    
    register_response = await client.post("/api/v1/auth/register", json=user_data)
    tokens = register_response.json()
    
    # Create a board
    board_data = {"title": "Test Board"}
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    create_response = await client.post("/api/v1/boards", json=board_data, headers=headers)
    board_id = create_response.json()["id"]
    
    # Get board
    response = await client.get(f"/api/v1/boards/{board_id}", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == board_id
    assert data["title"] == board_data["title"]


@pytest.mark.asyncio
async def test_update_board(client: AsyncClient):
    """Test updating a board."""
    # Register user and get token
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    
    register_response = await client.post("/api/v1/auth/register", json=user_data)
    tokens = register_response.json()
    
    # Create a board
    board_data = {"title": "Test Board"}
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    create_response = await client.post("/api/v1/boards", json=board_data, headers=headers)
    board_id = create_response.json()["id"]
    
    # Update board
    update_data = {"title": "Updated Board", "description": "Updated description"}
    response = await client.patch(f"/api/v1/boards/{board_id}", json=update_data, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == update_data["title"]
    assert data["description"] == update_data["description"]


@pytest.mark.asyncio
async def test_delete_board(client: AsyncClient):
    """Test deleting a board."""
    # Register user and get token
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }
    
    register_response = await client.post("/api/v1/auth/register", json=user_data)
    tokens = register_response.json()
    
    # Create a board
    board_data = {"title": "Test Board"}
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    create_response = await client.post("/api/v1/boards", json=board_data, headers=headers)
    board_id = create_response.json()["id"]
    
    # Delete board
    response = await client.delete(f"/api/v1/boards/{board_id}", headers=headers)
    
    assert response.status_code == 204
    
    # Verify board is deleted
    get_response = await client.get(f"/api/v1/boards/{board_id}", headers=headers)
    assert get_response.status_code == 404

