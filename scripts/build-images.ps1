# Script para construir todas las imágenes Docker
# Ejecutar desde la raíz del proyecto

Write-Host "🐳 Construyendo imágenes Docker..." -ForegroundColor Cyan

# Collector
Write-Host "`n📰 Construyendo Collector..." -ForegroundColor Yellow
docker build -t newscolcap/collector:latest ./services/collector

# Processor
Write-Host "`n⚙️ Construyendo Processor..." -ForegroundColor Yellow
docker build -t newscolcap/processor:latest ./services/processor

# Analyzer
Write-Host "`n📊 Construyendo Analyzer..." -ForegroundColor Yellow
docker build -t newscolcap/analyzer:latest ./services/analyzer

# API
Write-Host "`n🌐 Construyendo API..." -ForegroundColor Yellow
docker build -t newscolcap/api:latest ./services/api

Write-Host "`n✅ Todas las imágenes construidas exitosamente!" -ForegroundColor Green
Write-Host "`nPara ver las imágenes:" -ForegroundColor Cyan
Write-Host "  docker images | Select-String newscolcap" -ForegroundColor White
