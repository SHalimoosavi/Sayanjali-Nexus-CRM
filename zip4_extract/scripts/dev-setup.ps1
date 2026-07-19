# One-time local setup for Sayanjali Nexus CRM (Windows PowerShell)
Set-Location backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
alembic upgrade head
python scripts/seed.py
Set-Location ..

Set-Location frontend
npm install
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
Set-Location ..

Write-Host "Setup complete."
Write-Host "Run: cd backend; .venv\Scripts\Activate.ps1; uvicorn app.main:app --reload"
Write-Host "Run: cd frontend; npm run dev"
