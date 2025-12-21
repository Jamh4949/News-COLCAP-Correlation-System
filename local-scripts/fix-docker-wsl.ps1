# Script para arreglar problemas de Docker Desktop con WSL

Write-Host "🔧 Arreglando Docker Desktop + WSL2" -ForegroundColor Cyan

Write-Host "`nPaso 1: Cerrando Docker Desktop..." -ForegroundColor Yellow
Stop-Process -Name "Docker Desktop" -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 3

Write-Host "Paso 2: Apagando WSL completamente..." -ForegroundColor Yellow
wsl --shutdown
Start-Sleep -Seconds 3

Write-Host "Paso 3: Actualizando WSL..." -ForegroundColor Yellow
wsl --update

Write-Host "Paso 4: Configurando WSL 2 como predeterminado..." -ForegroundColor Yellow
wsl --set-default-version 2

Write-Host "Paso 5: Reiniciando Docker Desktop..." -ForegroundColor Yellow
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"

Write-Host "`n⏳ Esperando 30 segundos a que Docker Desktop inicie..." -ForegroundColor Cyan
Start-Sleep -Seconds 30

Write-Host "`nVerificando estado..." -ForegroundColor Yellow
docker version

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Docker Desktop funciona correctamente!" -ForegroundColor Green
    Write-Host "Ahora puedes ejecutar: .\scripts\start-local.ps1" -ForegroundColor Cyan
} else {
    Write-Host "`n⚠️ Docker aún no está listo. Espera 1 minuto más y ejecuta:" -ForegroundColor Yellow
    Write-Host "  docker version" -ForegroundColor White
    Write-Host "`nSi sigue fallando, usa la opción sin Docker:" -ForegroundColor Yellow
    Write-Host "  .\run-local-no-docker.ps1" -ForegroundColor White
}
