# Script de Validacion del Proyecto
# Verifica que todos los archivos necesarios esten presentes

Write-Host "Validando estructura del proyecto..." -ForegroundColor Cyan

$errors = 0
$warnings = 0

# Funcion para verificar archivo
function Test-ProjectFile {
    param($path, $description)
    if (Test-Path $path) {
        Write-Host "  [OK] $description" -ForegroundColor Green
        return $true
    } else {
        Write-Host "  [FALTA] $description" -ForegroundColor Red
        Write-Host "     Ruta: $path" -ForegroundColor Gray
        $script:errors++
        return $false
    }
}

# Verificar archivos raiz
Write-Host "`n[Archivos de configuracion]" -ForegroundColor Yellow
Test-ProjectFile "README.md" "README.md"
Test-ProjectFile "QUICKSTART.md" "Quick Start Guide"
Test-ProjectFile "INSTALL.md" "Installation Guide"
Test-ProjectFile "TECHNICAL.md" "Technical Documentation"
Test-ProjectFile ".gitignore" ".gitignore"
Test-ProjectFile "docker-compose.yml" "Docker Compose"

# Verificar database
Write-Host "`n[Database]" -ForegroundColor Yellow
Test-ProjectFile "database\init.sql" "Init SQL Script"

# Verificar scripts
Write-Host "`n[Scripts]" -ForegroundColor Yellow
Test-ProjectFile "scripts\build-images.ps1" "Build Images Script"
Test-ProjectFile "scripts\deploy-k8s.ps1" "Deploy K8s Script"
Test-ProjectFile "scripts\start-local.ps1" "Start Local Script"
Test-ProjectFile "scripts\test-apis.ps1" "Test APIs Script"

# Verificar Collector
Write-Host "`n[Collector Service]" -ForegroundColor Yellow
Test-ProjectFile "services\collector\Dockerfile" "Collector Dockerfile"
Test-ProjectFile "services\collector\main.py" "Collector Main"
Test-ProjectFile "services\collector\requirements.txt" "Collector Requirements"

# Verificar Processor
Write-Host "`n[Processor Service]" -ForegroundColor Yellow
Test-ProjectFile "services\processor\Dockerfile" "Processor Dockerfile"
Test-ProjectFile "services\processor\main.py" "Processor Main"
Test-ProjectFile "services\processor\requirements.txt" "Processor Requirements"

# Verificar Analyzer
Write-Host "`n[Analyzer Service]" -ForegroundColor Yellow
Test-ProjectFile "services\analyzer\Dockerfile" "Analyzer Dockerfile"
Test-ProjectFile "services\analyzer\main.py" "Analyzer Main"
Test-ProjectFile "services\analyzer\requirements.txt" "Analyzer Requirements"

# Verificar API
Write-Host "`n[API Service]" -ForegroundColor Yellow
Test-ProjectFile "services\api\Dockerfile" "API Dockerfile"
Test-ProjectFile "services\api\main.py" "API Main"
Test-ProjectFile "services\api\requirements.txt" "API Requirements"

# Verificar Kubernetes
Write-Host "`n[Kubernetes Manifests]" -ForegroundColor Yellow
Test-ProjectFile "k8s\00-namespace.yaml" "Namespace"
Test-ProjectFile "k8s\01-configmap.yaml" "ConfigMap"
Test-ProjectFile "k8s\02-secrets.yaml" "Secrets"
Test-ProjectFile "k8s\03-postgres-pvc.yaml" "PostgreSQL PVC"
Test-ProjectFile "k8s\04-postgres.yaml" "PostgreSQL"
Test-ProjectFile "k8s\05-redis.yaml" "Redis"
Test-ProjectFile "k8s\06-collector.yaml" "Collector Deployment"
Test-ProjectFile "k8s\07-processor.yaml" "Processor Deployment"
Test-ProjectFile "k8s\08-analyzer.yaml" "Analyzer Deployment"
Test-ProjectFile "k8s\09-api.yaml" "API Deployment"

# Verificar Docker esta instalado
Write-Host "`n[Prerequisitos]" -ForegroundColor Yellow
try {
    $dockerVersion = docker --version 2>$null
    if ($dockerVersion) {
        Write-Host "  [OK] Docker instalado: $dockerVersion" -ForegroundColor Green
    } else {
        Write-Host "  [WARN] Docker no encontrado" -ForegroundColor Yellow
        $script:warnings++
    }
} catch {
    Write-Host "  [WARN] Docker no encontrado" -ForegroundColor Yellow
    $script:warnings++
}

try {
    $composeVersion = docker-compose --version 2>$null
    if ($composeVersion) {
        Write-Host "  [OK] Docker Compose instalado: $composeVersion" -ForegroundColor Green
    } else {
        Write-Host "  [WARN] Docker Compose no encontrado" -ForegroundColor Yellow
        $script:warnings++
    }
} catch {
    Write-Host "  [WARN] Docker Compose no encontrado" -ForegroundColor Yellow
    $script:warnings++
}

try {
    $pythonVersion = python --version 2>$null
    if ($pythonVersion) {
        Write-Host "  [OK] Python instalado: $pythonVersion" -ForegroundColor Green
    } else {
        Write-Host "  [INFO] Python no encontrado (opcional)" -ForegroundColor Gray
    }
} catch {
    Write-Host "  [INFO] Python no encontrado (opcional)" -ForegroundColor Gray
}

# Resumen
Write-Host "`n" + ("=" * 60) -ForegroundColor Cyan
Write-Host "RESUMEN DE VALIDACION" -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan

if ($errors -eq 0) {
    Write-Host "[OK] Todos los archivos presentes!" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Faltan $errors archivo(s)" -ForegroundColor Red
}

if ($warnings -gt 0) {
    Write-Host "[WARN] $warnings advertencia(s)" -ForegroundColor Yellow
}

Write-Host "`nEstadisticas:" -ForegroundColor Cyan
$totalFiles = (Get-ChildItem -Recurse -File).Count
Write-Host "  Total de archivos en el proyecto: $totalFiles" -ForegroundColor White

Write-Host "`nSiguiente paso:" -ForegroundColor Cyan
if ($errors -eq 0) {
    Write-Host "  Ejecuta: .\scripts\start-local.ps1" -ForegroundColor White
    Write-Host "  O lee: QUICKSTART.md" -ForegroundColor White
} else {
    Write-Host "  Corrige los archivos faltantes primero" -ForegroundColor Red
}

Write-Host "`n" + ("=" * 60) -ForegroundColor Cyan

# Exit code
if ($errors -gt 0) {
    exit 1
} else {
    exit 0
}
