# Script para construir y subir imagenes a Amazon ECR

Write-Host "Construyendo y subiendo imagenes a AWS ECR..." -ForegroundColor Cyan

# Obtener Account ID
$ACCOUNT_ID = (aws sts get-caller-identity --query Account --output text)
$REGION = "us-east-1"
$ECR_BASE = "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"

if (-not $ACCOUNT_ID) {
    Write-Host "[ERROR] No se pudo obtener Account ID. Verifica AWS CLI configuracion." -ForegroundColor Red
    exit 1
}

Write-Host "`n[INFO] Account ID: $ACCOUNT_ID" -ForegroundColor Green
Write-Host "[INFO] Region: $REGION" -ForegroundColor Green
Write-Host "[INFO] ECR Base URL: $ECR_BASE`n" -ForegroundColor Green

# Login a ECR
Write-Host "[1/5] Autenticando con ECR..." -ForegroundColor Yellow
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_BASE

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Fallo la autenticacion con ECR" -ForegroundColor Red
    exit 1
}

# Construir y subir Collector
Write-Host "`n[2/5] Construyendo y subiendo Collector..." -ForegroundColor Yellow
docker build -t news-colcap/collector:latest ./services/collector
docker tag news-colcap/collector:latest "$ECR_BASE/news-colcap/collector:latest"
docker push "$ECR_BASE/news-colcap/collector:latest"

# Construir y subir Processor
Write-Host "`n[3/5] Construyendo y subiendo Processor..." -ForegroundColor Yellow
docker build -t news-colcap/processor:latest ./services/processor
docker tag news-colcap/processor:latest "$ECR_BASE/news-colcap/processor:latest"
docker push "$ECR_BASE/news-colcap/processor:latest"

# Construir y subir Analyzer
Write-Host "`n[4/5] Construyendo y subiendo Analyzer..." -ForegroundColor Yellow
docker build -t news-colcap/analyzer:latest ./services/analyzer
docker tag news-colcap/analyzer:latest "$ECR_BASE/news-colcap/analyzer:latest"
docker push "$ECR_BASE/news-colcap/analyzer:latest"

# Construir y subir API
Write-Host "`n[5/5] Construyendo y subiendo API..." -ForegroundColor Yellow
docker build -t news-colcap/api:latest ./services/api
docker tag news-colcap/api:latest "$ECR_BASE/news-colcap/api:latest"
docker push "$ECR_BASE/news-colcap/api:latest"

Write-Host "`n[OK] Todas las imagenes subidas exitosamente a ECR!" -ForegroundColor Green
Write-Host "`nURIs de las imagenes:" -ForegroundColor Cyan
Write-Host "  Collector: $ECR_BASE/news-colcap/collector:latest" -ForegroundColor White
Write-Host "  Processor: $ECR_BASE/news-colcap/processor:latest" -ForegroundColor White
Write-Host "  Analyzer:  $ECR_BASE/news-colcap/analyzer:latest" -ForegroundColor White
Write-Host "  API:       $ECR_BASE/news-colcap/api:latest" -ForegroundColor White

Write-Host "`n[INFO] Actualiza los manifiestos de K8s con estas URIs antes de desplegar." -ForegroundColor Yellow
