#!/bin/bash
set -e

echo "========================================="
echo "  Auto-Ads Backend Starting..."
echo "========================================="

echo "[1/3] Running database migrations..."
alembic upgrade head

echo "[2/3] Seeding default admin user..."
python seed.py

echo "[3/3] Starting FastAPI server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload