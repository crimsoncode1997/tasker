#!/bin/bash

# Run all tests
echo "Running tests..."

# Check if containers are running
if ! docker-compose -f docker-compose.dev.yml ps backend | grep -q "Up"; then
    echo "Error: Backend container is not running. Please start the development environment first."
    exit 1
fi

if ! docker-compose -f docker-compose.dev.yml ps frontend | grep -q "Up"; then
    echo "Error: Frontend container is not running. Please start the development environment first."
    exit 1
fi

echo "Running backend tests..."
docker-compose -f docker-compose.dev.yml exec backend pytest

echo "Running frontend tests..."
docker-compose -f docker-compose.dev.yml exec frontend npm test

echo "All tests completed!"

