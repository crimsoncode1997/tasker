# Tasker - Trello Clone

A production-ready Trello clone built with FastAPI, React, and PostgreSQL.

## Features

- 🔐 JWT Authentication with refresh tokens
- 📋 Board, List, and Card management
- 🎯 Drag & Drop functionality
- 👥 Board collaboration
- 🔍 Search functionality
- 📱 Responsive design
- 🐳 Dockerized deployment
- ✅ Comprehensive testing

## Tech Stack

### Backend
- FastAPI (Python)
- SQLAlchemy + Alembic
- PostgreSQL with asyncpg
- JWT authentication
- Pytest for testing

### Frontend
- React 18+ with TypeScript
- Vite
- Tailwind CSS
- dnd-kit for drag & drop
- TanStack Query for state management

### DevOps
- Docker & Docker Compose
- GitHub Actions CI/CD
- Pre-commit hooks

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Git

### Local Development

1. Clone the repository:
```bash
git clone <repository-url>
cd tasker
```

2. Copy environment variables:
```bash
cp env.example .env
# Edit .env with your configuration if needed
```

3. Start the development environment:
```bash
# Using Docker Compose
docker-compose -f docker-compose.dev.yml up --build

# Or using Makefile
make start

# Or using scripts
./scripts/start.sh
```

4. Run database migrations:
```bash
# Using Docker Compose
docker-compose -f docker-compose.dev.yml exec backend alembic upgrade head

# Or using Makefile
make migrate

# Or using scripts
./scripts/migrate.sh
```

5. (Optional) Seed with sample data:
```bash
# Using Docker Compose
docker-compose -f docker-compose.dev.yml exec backend python -m app.scripts.seed_data

# Or using Makefile
make seed

# Or using scripts
./scripts/seed.sh
```

6. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Database: localhost:5432

**Demo Credentials (after seeding):**
- Email: demo@tasker.com
- Password: demo123

### Manual Setup (Alternative)

1. Install dependencies:
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Run database migrations:
```bash
cd backend
alembic upgrade head
```

4. Start the services:
```bash
# Backend
cd backend
uvicorn app.main:app --reload

# Frontend (in another terminal)
cd frontend
npm run dev
```

## API Documentation

The API documentation is automatically generated and available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

### Backend Tests
```bash
# Using Docker Compose
docker-compose -f docker-compose.dev.yml exec backend pytest

# Or using Makefile
make test-backend

# Or manually
cd backend
pytest
```

### Frontend Tests
```bash
# Using Docker Compose
docker-compose -f docker-compose.dev.yml exec frontend npm test

# Or using Makefile
make test-frontend

# Or manually
cd frontend
npm test
```

### E2E Tests
```bash
# Using Docker Compose
docker-compose -f docker-compose.dev.yml exec frontend npm run test:e2e

# Or using Makefile
make test-e2e

# Or manually
cd frontend
npm run test:e2e
```

### All Tests
```bash
# Using Makefile
make test

# Or using scripts
./scripts/test.sh
```

## Scripts

Use the provided scripts for common tasks:

```bash
# Start development environment
./scripts/start.sh

# Run migrations
./scripts/migrate.sh

# Seed database with sample data
./scripts/seed.sh

# Run tests
./scripts/test.sh

# Run linters
./scripts/lint.sh

# Build for production
./scripts/build.sh
```

## Makefile Commands

For convenience, you can also use the Makefile:

```bash
# Development
make start          # Start development environment
make stop           # Stop development environment
make migrate        # Run database migrations
make seed           # Seed database with sample data

# Testing
make test           # Run all tests
make test-backend   # Run backend tests only
make test-frontend  # Run frontend tests only
make test-e2e       # Run E2E tests only

# Linting
make lint           # Run all linters
make lint-backend   # Run backend linters only
make lint-frontend  # Run frontend linters only

# Production
make build          # Build production images
make deploy         # Deploy to production

# Utilities
make logs           # Show logs from all services
make clean          # Clean up containers and volumes
make shell-backend  # Access backend container shell
make shell-frontend # Access frontend container shell
make shell-db       # Access database shell
```

## Environment Variables

See `env.example` for all required environment variables.

Key variables:
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT secret key (generate a strong secret for production)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Access token expiration time (default: 30)
- `REFRESH_TOKEN_EXPIRE_DAYS`: Refresh token expiration time (default: 7)
- `FRONTEND_URL`: Frontend URL for CORS
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`: Database credentials
- `ENVIRONMENT`: Environment mode (development/production)
- `DEBUG`: Enable debug mode (true/false)

## Project Structure

```
tasker/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Core configuration
│   │   ├── models/         # Database models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   └── tests/          # Backend tests
│   ├── alembic/            # Database migrations
│   └── requirements.txt
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # Reusable components
│   │   ├── features/       # Feature-specific code
│   │   ├── hooks/          # Custom hooks
│   │   ├── services/       # API services
│   │   └── tests/          # Frontend tests
│   └── package.json
├── scripts/                # Utility scripts
├── docker-compose.dev.yml  # Development environment
└── .github/workflows/      # CI/CD workflows
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linters
5. Submit a pull request

## License

MIT License
