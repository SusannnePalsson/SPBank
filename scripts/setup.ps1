Param(
    [switch]$WithDocker
)

Write-Host "=== TheBankProject setup ===" -ForegroundColor Cyan

# 1) Create venv
if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
  py -m venv .venv
}
.\.venv\Scripts\Activate

# 2) Install deps
pip install -r requirements.txt

# 3) .env
if (-not (Test-Path ".\.env")) {
  Copy-Item .\.env.example .\.env
  Write-Host "Created .env from .env.example" -ForegroundColor Yellow
}

# 4) Optional: docker compose up
if ($WithDocker) {
  if (Get-Command docker -ErrorAction SilentlyContinue) {
    Write-Host "Starting Postgres + pgAdmin via Docker..." -ForegroundColor Cyan
    docker compose up -d
  } else {
    Write-Host "Docker is not installed or not in PATH. Skipping docker compose." -ForegroundColor Yellow
  }
}

# 5) Init schema
python init_schema.py

Write-Host "=== Setup complete. You can now run: python flow_main.py ===" -ForegroundColor Green
