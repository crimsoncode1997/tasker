#!/bin/bash

# Build production images
echo "Building production images..."

# Build backend image
echo "Building backend image..."
docker build -f backend/Dockerfile -t tasker-backend ./backend

# Build frontend image
echo "Building frontend image..."
docker build -f frontend/Dockerfile -t tasker-frontend ./frontend

echo "Production images built successfully!"
echo "Backend image: tasker-backend"
echo "Frontend image: tasker-frontend"

