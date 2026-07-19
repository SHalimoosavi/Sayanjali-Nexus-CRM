#!/usr/bin/env bash
# One-time local setup for Sayanjali Nexus CRM (macOS/Linux).
# Windows users: see scripts/dev-setup.ps1
set -e

echo "== Backend =="
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp -n .env.example .env || true
alembic upgrade head
python scripts/seed.py
cd ..

echo "== Frontend =="
cd frontend
npm install
cp -n .env.example .env || true
cd ..

echo "Setup complete."
echo "Run:  cd backend && source .venv/bin/activate && uvicorn app.main:app --reload"
echo "Run:  cd frontend && npm run dev"
