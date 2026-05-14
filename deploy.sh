#!/bin/bash
set -e

echo "==> Pulling latest code..."
git pull origin main

echo "==> Building & starting services..."
docker compose pull postgres minio
docker compose build api
docker compose up -d

echo "==> Waiting for API to be ready..."
sleep 5
curl -sf http://localhost:8080/health && echo " OK" || echo " Not ready yet, check: docker compose logs api"
