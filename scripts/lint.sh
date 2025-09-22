#!/bin/bash

# Run linters
echo "Running linters..."

# Check if containers are running
if ! docker-compose -f docker-compose.dev.yml ps backend | grep -q "Up"; then
    echo "Error: Backend container is not running. Please start the development environment first."
    exit 1
fi

if ! docker-compose -f docker-compose.dev.yml ps frontend | grep -q "Up"; then
    echo "Error: Frontend container is not running. Please start the development environment first."
    exit 1
fi

echo "Running backend linters..."
docker-compose -f docker-compose.dev.yml exec backend black .
docker-compose -f docker-compose.dev.yml exec backend isort .
docker-compose -f docker-compose.dev.yml exec backend flake8

echo "Running frontend linters..."
docker-compose -f docker-compose.dev.yml exec frontend npm run lint

echo "All linters completed!"

