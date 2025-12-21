# Script para crear repositorios ECR

Write-Host "Creando repositorios en Amazon ECR..." -ForegroundColor Cyan

$REGION = "us-east-1"
$REPOS = @("collector", "processor", "analyzer", "api")

foreach ($repo in $REPOS) {
    Write-Host "`nCreando repositorio: news-colcap/$repo" -ForegroundColor Yellow
    
    aws ecr create-repository `
        --repository-name "news-colcap/$repo" `
        --region $REGION `
        --image-scanning-configuration scanOnPush=true 2>$null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Repositorio news-colcap/$repo creado" -ForegroundColor Green
    } else {
        Write-Host "[WARN] Repositorio news-colcap/$repo ya existe o error al crear" -ForegroundColor Yellow
    }
}

Write-Host "`n[OK] Repositorios ECR configurados!" -ForegroundColor Green
Write-Host "`nProximo paso:" -ForegroundColor Cyan
Write-Host "  Ejecuta: .\scripts\build-and-push-ecr.ps1" -ForegroundColor White
