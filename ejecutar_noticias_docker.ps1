<#
.SYNOPSIS
    Script maestro para ejecutar el pipeline completo de noticias con Docker.

.PARAMETER Clean
    Elimina todos los contenedores y volumenes anteriores

.PARAMETER SkipColcap
    Salta la generacion e importacion de datos COLCAP

.PARAMETER SkipBuild
    No reconstruye las imagenes Docker

.PARAMETER NoLogs
    No muestra logs despues del despliegue

.PARAMETER NoBrowser
    No abre el navegador automaticamente
#>

param(
    [switch]$Clean,
    [switch]$SkipColcap,
    [switch]$SkipBuild,
    [switch]$NoLogs,
    [switch]$NoBrowser
)

function Write-Step {
    param([string]$Message, [int]$Step)
    Write-Host "`n============================================================" -ForegroundColor Cyan
    Write-Host "PASO $Step : $Message" -ForegroundColor Yellow
    Write-Host "============================================================`n" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Write-Error2 {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Write-Warning2 {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

# Banner
Write-Host "`n============================================================" -ForegroundColor Magenta
Write-Host "   PIPELINE COMPLETO DE NOTICIAS - MODO DOCKER" -ForegroundColor Magenta
Write-Host "============================================================`n" -ForegroundColor Magenta

$StopWatch = [System.Diagnostics.Stopwatch]::StartNew()

# PASO 0: Verificar Docker
Write-Step "VERIFICACION DE DOCKER" 0

Write-Info "Verificando Docker Desktop..."
$dockerRunning = docker info 2>$null
if (!$?) {
    Write-Error2 "Docker no esta corriendo o no esta instalado"
    Write-Warning2 "Por favor, inicia Docker Desktop y vuelve a intentar"
    exit 1
}

Write-Success "Docker esta corriendo"

Write-Info "Verificando docker-compose..."
docker-compose version 2>$null
if (!$?) {
    Write-Error2 "docker-compose no esta disponible"
    exit 1
}
Write-Success "docker-compose disponible"

# PASO 1: Limpieza
if ($Clean) {
    Write-Step "LIMPIEZA DE CONTENEDORES ANTERIORES" 1
    
    Write-Warning2 "Deteniendo y eliminando contenedores, redes y volumenes anteriores..."
    docker-compose down -v
    
    if ($?) {
        Write-Success "Limpieza completada"
    } else {
        Write-Warning2 "No habia contenedores previos o hubo un error menor"
    }
}

# PASO 2: Generar datos COLCAP
if (!$SkipColcap) {
    Write-Step "GENERACION DE DATOS COLCAP" 2
    
    Write-Info "Ejecutando script de descarga de COLCAP..."
    python ".\local-scripts\get_colcap.py"
    
    if ($?) {
        Write-Success "Datos COLCAP generados"
    } else {
        Write-Error2 "Error al generar datos COLCAP"
        Write-Warning2 "Continuando de todas formas..."
    }
}

# PASO 3: Construir imagenes
if (!$SkipBuild) {
    Write-Step "CONSTRUCCION DE IMAGENES DOCKER" 3
    
    Write-Info "Construyendo imagenes (esto puede tardar unos minutos)..."
    docker-compose build
    
    if (!$?) {
        Write-Error2 "Error al construir imagenes Docker"
        exit 1
    }
    Write-Success "Imagenes construidas exitosamente"
} else {
    Write-Warning2 "Saltando construccion de imagenes (usando existentes)"
}

# PASO 4: Levantar servicios
Write-Step "LEVANTANDO SERVICIOS DOCKER" 4

Write-Info "Iniciando todos los servicios con docker-compose..."
docker-compose up -d

if (!$?) {
    Write-Error2 "Error al levantar servicios"
    exit 1
}

Write-Success "Servicios iniciados"
Write-Info "Esperando 10 segundos para que los servicios inicialicen..."
Start-Sleep -Seconds 10

# PASO 5: Verificar estado
Write-Step "VERIFICACION DE SERVICIOS" 5

Write-Info "Estado de los contenedores:"
docker-compose ps

$services = @("postgres", "redis", "collector", "processor", "analyzer", "api")

foreach ($service in $services) {
    $status = docker-compose ps $service 2>$null | Select-String -Pattern "Up|running" -Quiet
    if ($status) {
        Write-Success "$service esta corriendo"
    } else {
        Write-Warning2 "$service no esta corriendo o no responde"
    }
}

# PASO 6: Importar datos COLCAP
if (!$SkipColcap) {
    Write-Step "IMPORTACION DE DATOS COLCAP A DOCKER" 6
    
    Write-Info "Esperando a que PostgreSQL este listo..."
    Start-Sleep -Seconds 5
    
    Write-Info "Importando datos COLCAP a la base de datos Docker..."
    python ".\local-scripts\import_colcap.py"
    
    if ($?) {
        Write-Success "Datos COLCAP importados a PostgreSQL"
    } else {
        Write-Warning2 "Error al importar COLCAP (puede que ya existan datos)"
    }
}

# PASO 7: Verificar API
Write-Step "VERIFICACION DE API" 7

Write-Info "Esperando a que la API este lista..."
Start-Sleep -Seconds 3

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -TimeoutSec 5 -UseBasicParsing 2>$null
    if ($response.StatusCode -eq 200) {
        Write-Success "API respondiendo correctamente"
    }
} catch {
    Write-Warning2 "API no responde aun"
}

# PASO 8: Abrir navegador
if (!$NoBrowser) {
    Write-Step "ABRIENDO DASHBOARD" 8
    
    Write-Info "Abriendo dashboard en navegador..."
    Start-Process "http://localhost:8000"
    Write-Success "Dashboard abierto"
}

# Resumen final
$elapsed = $StopWatch.Elapsed
Write-Host "`n============================================================" -ForegroundColor Green
Write-Host "        PIPELINE COMPLETADO EXITOSAMENTE" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green

Write-Host "`nTiempo total: $($elapsed.Minutes)m $($elapsed.Seconds)s`n" -ForegroundColor Cyan

Write-Host "SERVICIOS DISPONIBLES:" -ForegroundColor Yellow
Write-Host "   Dashboard:      http://localhost:8000" -ForegroundColor Cyan
Write-Host "   API Docs:       http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "   Health Check:   http://localhost:8000/api/health" -ForegroundColor Cyan

Write-Host "`nCOMANDOS UTILES:" -ForegroundColor Yellow
Write-Host "   Ver logs:         docker-compose logs -f" -ForegroundColor Gray
Write-Host "   Estado:           docker-compose ps" -ForegroundColor Gray
Write-Host "   Detener todo:     docker-compose down`n" -ForegroundColor Gray

# Mostrar logs
if (!$NoLogs) {
    Write-Warning2 "Mostrando logs en tiempo real (Ctrl+C para salir)...`n"
    
    try {
        docker-compose logs -f
    } catch {
        Write-Info "Logs interrumpidos por el usuario"
    }
} else {
    Write-Host "Para ver logs ejecuta: docker-compose logs -f`n" -ForegroundColor Gray
}
