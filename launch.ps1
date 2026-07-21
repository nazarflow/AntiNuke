param(
    [switch]$Update,
    [switch]$Stop,
    [switch]$Logs
)

$ErrorActionPreference = "Stop"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host " AntiNuke Bot - Launch Manager (Docker)" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

if ($Stop) {
    Write-Host "[*] Stopping containers..." -ForegroundColor Yellow
    docker compose down
    Write-Host "[+] Containers stopped." -ForegroundColor Green
    exit
}

if ($Update) {
    Write-Host "[*] Pulling latest changes from git..." -ForegroundColor Yellow
    git pull origin develop

    Write-Host "[*] Rebuilding Docker images..." -ForegroundColor Yellow
    docker compose build --no-cache
}

Write-Host "[*] Starting Docker containers in background..." -ForegroundColor Yellow
docker compose up -d

Write-Host "[+] All systems go! Bot and Database are running." -ForegroundColor Green

if ($Logs) {
    Write-Host "[*] Tailing logs (Press Ctrl+C to stop viewing)..." -ForegroundColor Yellow
    docker compose logs -f bot
} else {
    Write-Host ""
    Write-Host "Useful commands:" -ForegroundColor Cyan
    Write-Host "  .\launch.ps1 -Logs    (View bot logs in real-time)"
    Write-Host "  .\launch.ps1 -Stop    (Stop all containers)"
    Write-Host "  .\launch.ps1 -Update  (Pull git updates and rebuild containers)"
}
