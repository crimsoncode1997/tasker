#!/bin/bash

# Run database migrations
echo "Running database migrations..."

# Check if backend container is running
if ! docker-compose -f docker-compose.dev.yml ps backend | grep -q "Up"; then
    echo "Error: Backend container is not running. Please start the development environment first."
    exit 1
fi

# Run migrations
docker-compose -f docker-compose.dev.yml exec backend alembic upgrade head

echo "Migrations completed successfully!"

