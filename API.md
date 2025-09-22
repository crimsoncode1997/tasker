# Tasker API Documentation

## Overview

Tasker is a production-ready Trello clone built with FastAPI, React, and PostgreSQL. This document provides comprehensive API documentation with examples.

## Base URL

- Development: `http://localhost:8000/api/v1`
- Production: `https://your-domain.com/api/v1`

## Authentication

The API uses JWT (JSON Web Token) authentication with access and refresh tokens.

### Headers

All authenticated requests must include:
```
Authorization: Bearer <access_token>
```

## API Endpoints

### Authentication

#### Register User
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123",
  "full_name": "John Doe"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

#### Login User
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

#### Refresh Token
```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### Get Current User
```http
GET /auth/me
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

### Boards

#### Get User's Boards
```http
GET /boards?skip=0&limit=100
Authorization: Bearer <access_token>
```

**Response:**
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "title": "My Project",
    "description": "Project description",
    "owner_id": "123e4567-e89b-12d3-a456-426614174000",
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00",
    "owner": {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "email": "user@example.com",
      "full_name": "John Doe",
      "is_active": true,
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00"
    },
    "lists": []
  }
]
```

#### Create Board
```http
POST /boards
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "title": "New Board",
  "description": "Board description"
}
```

#### Get Board by ID
```http
GET /boards/{board_id}
Authorization: Bearer <access_token>
```

#### Update Board
```http
PATCH /boards/{board_id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "title": "Updated Title",
  "description": "Updated description"
}
```

#### Delete Board
```http
DELETE /boards/{board_id}
Authorization: Bearer <access_token>
```

#### Invite User to Board
```http
POST /boards/{board_id}/invite
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "email": "user@example.com",
  "role": "member"
}
```

### Lists

#### Create List
```http
POST /lists
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "title": "New List",
  "board_id": "123e4567-e89b-12d3-a456-426614174000",
  "position": 1.0
}
```

#### Get List by ID
```http
GET /lists/{list_id}
Authorization: Bearer <access_token>
```

#### Update List
```http
PATCH /lists/{list_id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "title": "Updated List Title",
  "position": 2.0
}
```

#### Delete List
```http
DELETE /lists/{list_id}
Authorization: Bearer <access_token>
```

#### Reorder Lists
```http
PATCH /lists/reorder?board_id={board_id}
Authorization: Bearer <access_token>
Content-Type: application/json

[
  {
    "list_id": "123e4567-e89b-12d3-a456-426614174000",
    "position": 1.0
  },
  {
    "list_id": "123e4567-e89b-12d3-a456-426614174001",
    "position": 2.0
  }
]
```

### Cards

#### Create Card
```http
POST /cards
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "title": "New Card",
  "description": "Card description",
  "list_id": "123e4567-e89b-12d3-a456-426614174000",
  "position": 1.0,
  "assignee_id": "123e4567-e89b-12d3-a456-426614174000",
  "due_date": "2024-12-31"
}
```

#### Get Card by ID
```http
GET /cards/{card_id}
Authorization: Bearer <access_token>
```

#### Update Card
```http
PATCH /cards/{card_id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "title": "Updated Card Title",
  "description": "Updated description",
  "position": 2.0,
  "assignee_id": "123e4567-e89b-12d3-a456-426614174000",
  "due_date": "2024-12-31"
}
```

#### Delete Card
```http
DELETE /cards/{card_id}
Authorization: Bearer <access_token>
```

#### Move Card
```http
PATCH /cards/move
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "card_id": "123e4567-e89b-12d3-a456-426614174000",
  "list_id": "123e4567-e89b-12d3-a456-426614174001",
  "position": 1.0
}
```

#### Reorder Cards
```http
PATCH /cards/reorder?list_id={list_id}
Authorization: Bearer <access_token>
Content-Type: application/json

[
  {
    "card_id": "123e4567-e89b-12d3-a456-426614174000",
    "position": 1.0
  },
  {
    "card_id": "123e4567-e89b-12d3-a456-426614174001",
    "position": 2.0
  }
]
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Validation error message"
}
```

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 403 Forbidden
```json
{
  "detail": "Not enough permissions"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## Rate Limiting

The API implements rate limiting:
- 100 requests per minute per IP address
- Rate limit headers are included in responses:
  - `X-RateLimit-Limit`: Maximum requests allowed
  - `X-RateLimit-Remaining`: Requests remaining in current window
  - `X-RateLimit-Reset`: Time when the rate limit resets

## Examples

### Complete Workflow Example

1. **Register a new user:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "password123",
    "full_name": "John Doe"
  }'
```

2. **Create a board:**
```bash
curl -X POST "http://localhost:8000/api/v1/boards" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "title": "My Project Board",
    "description": "A board for managing my project tasks"
  }'
```

3. **Create a list:**
```bash
curl -X POST "http://localhost:8000/api/v1/lists" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "title": "To Do",
    "board_id": "BOARD_ID",
    "position": 1.0
  }'
```

4. **Create a card:**
```bash
curl -X POST "http://localhost:8000/api/v1/cards" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "title": "Setup development environment",
    "description": "Install and configure all necessary tools",
    "list_id": "LIST_ID",
    "position": 1.0,
    "due_date": "2024-12-31"
  }'
```

## Interactive API Documentation

When running the application, you can access interactive API documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

These interfaces allow you to test API endpoints directly from your browser.

