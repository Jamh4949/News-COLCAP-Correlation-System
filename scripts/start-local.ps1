# Script para pruebas locales con Docker Compose

Write-Host "🚀 Iniciando servicios con Docker Compose..." -ForegroundColor Cyan

# Verificar que Docker está corriendo
if (-not (docker info 2>$null)) {
    Write-Host "❌ Docker no está corriendo. Por favor inicia Docker Desktop." -ForegroundColor Red
    exit 1
}

# Detener contenedores existentes
Write-Host "`n🛑 Deteniendo contenedores existentes..." -ForegroundColor Yellow
docker-compose down

# Construir imágenes
Write-Host "`n🔨 Construyendo imágenes..." -ForegroundColor Yellow
docker-compose build

# Iniciar servicios
Write-Host "`n▶️ Iniciando servicios..." -ForegroundColor Yellow
docker-compose up -d

# Esperar a que los servicios estén listos
Write-Host "`n⏳ Esperando a que los servicios estén listos..." -ForegroundColor Cyan
Start-Sleep -Seconds 10

# Mostrar estado
Write-Host "`n📊 Estado de los contenedores:" -ForegroundColor Cyan
docker-compose ps

Write-Host "`n✅ Servicios iniciados!" -ForegroundColor Green
Write-Host "`n🌐 Accede al dashboard en:" -ForegroundColor Yellow
Write-Host "  http://localhost:8000" -ForegroundColor White

Write-Host "`n📝 Ver logs:" -ForegroundColor Cyan
Write-Host "  docker-compose logs -f [servicio]" -ForegroundColor White
Write-Host "`nServicios disponibles: collector, processor, analyzer, api" -ForegroundColor Gray
