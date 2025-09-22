#!/bin/bash

# Seed database with sample data
echo "Seeding database with sample data..."

# Check if backend container is running
if ! docker-compose -f docker-compose.dev.yml ps backend | grep -q "Up"; then
    echo "Error: Backend container is not running. Please start the development environment first."
    exit 1
fi

# Run seed script
docker-compose -f docker-compose.dev.yml exec backend python -m app.scripts.seed_data

echo "Database seeded successfully!"

