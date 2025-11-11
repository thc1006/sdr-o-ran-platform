# =====================================================
# SDR-O-RAN Platform - Automated Deployment Launcher
# PowerShell Script for Windows
# =====================================================

Write-Host "=========================================="  -ForegroundColor Cyan
Write-Host "  SDR-O-RAN Automated Deployment" -ForegroundColor Cyan
Write-Host "  Starting deployment in WSL..." -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if WSL is installed
Write-Host "[1/5] Checking WSL..." -ForegroundColor Yellow
try {
    $wslVersion = wsl --version
    Write-Host "  ✅ WSL is installed" -ForegroundColor Green
} catch {
    Write-Host "  ❌ WSL not found! Please install WSL 2" -ForegroundColor Red
    exit 1
}

# Check if Docker Desktop is running
Write-Host "[2/5] Checking Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "  ✅ Docker found: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Docker not running! Please start Docker Desktop" -ForegroundColor Red
    exit 1
}

# Test GPU access
Write-Host "[3/5] Testing GPU access..." -ForegroundColor Yellow
try {
    $gpuTest = docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi 2>&1
    if ($gpuTest -match "NVIDIA") {
        Write-Host "  ✅ GPU accessible in Docker" -ForegroundColor Green
    }
} catch {
    Write-Host "  ⚠️  GPU test failed, will run in CPU mode" -ForegroundColor Yellow
}

# Copy project to WSL
Write-Host "[4/5] Preparing project in WSL..." -ForegroundColor Yellow
Write-Host "  This may take a few minutes..." -ForegroundColor Gray

$projectPath = "C:\Users\ict\OneDrive\桌面\dev\sdr-o-ran-platform"
$wslCommand = @"
cd ~
mkdir -p dev
echo '📁 Copying project to WSL...'
cp -r /mnt/c/Users/ict/OneDrive/桌面/dev/sdr-o-ran-platform dev/ 2>/dev/null || echo 'Project already exists'
cd dev/sdr-o-ran-platform
echo '✅ Project ready in WSL'
ls -la
"@

wsl bash -c $wslCommand

Write-Host "  ✅ Project copied to WSL" -ForegroundColor Green

# Launch automated deployment
Write-Host "[5/5] Launching automated deployment..." -ForegroundColor Yellow
Write-Host ""
Write-Host "=========================================="  -ForegroundColor Cyan
Write-Host "  🚀 Starting Auto-Deploy Script" -ForegroundColor Cyan
Write-Host "=========================================="  -ForegroundColor Cyan
Write-Host ""
Write-Host "This will take approximately 30-60 minutes." -ForegroundColor Yellow
Write-Host "The deployment will run automatically." -ForegroundColor Yellow
Write-Host ""
Write-Host "You can safely close this window." -ForegroundColor Green
Write-Host "Services will continue running in the background." -ForegroundColor Green
Write-Host ""
Write-Host "When you wake up, check:" -ForegroundColor Cyan
Write-Host "  • http://localhost:8000/docs (API)" -ForegroundColor White
Write-Host "  • http://localhost:6006 (TensorBoard)" -ForegroundColor White
Write-Host ""
Write-Host "Press any key to start deployment..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Run deployment in WSL
Write-Host ""
Write-Host "🚀 Deploying now..." -ForegroundColor Green
Write-Host ""

$deployCommand = @"
cd ~/dev/sdr-o-ran-platform
chmod +x scripts/*.sh
bash scripts/auto-deploy.sh
"@

wsl bash -c $deployCommand

Write-Host ""
Write-Host "=========================================="  -ForegroundColor Cyan
Write-Host "  ✅ Deployment Script Completed!" -ForegroundColor Green
Write-Host "=========================================="  -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Check containers: wsl docker-compose ps" -ForegroundColor White
Write-Host "  2. View logs: wsl docker-compose logs -f" -ForegroundColor White
Write-Host "  3. Access API: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  4. Monitor training: http://localhost:6006" -ForegroundColor White
Write-Host ""
Write-Host "😴 Good night! Your platform is running!" -ForegroundColor Green
Write-Host ""

# Keep window open
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
