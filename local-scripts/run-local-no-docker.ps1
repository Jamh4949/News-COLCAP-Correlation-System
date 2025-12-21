# Script para ejecutar servicios SIN Docker
# Útil cuando Docker tiene problemas

Write-Host "🐍 Ejecutando proyecto sin Docker" -ForegroundColor Cyan
Write-Host "Instalando dependencias..." -ForegroundColor Yellow

# Verificar Python
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Python no encontrado. Instala Python 3.11+" -ForegroundColor Red
    exit 1
}
Write-Host "✓ $pythonVersion" -ForegroundColor Green

# Crear entorno virtual si no existe
if (-not (Test-Path "venv")) {
    Write-Host "Creando entorno virtual..." -ForegroundColor Yellow
    python -m venv venv
}

# Activar entorno virtual
Write-Host "Activando entorno virtual..." -ForegroundColor Yellow
.\venv\Scripts\Activate.ps1

# Instalar dependencias de todos los servicios
Write-Host "`nInstalando dependencias..." -ForegroundColor Yellow

$services = @("collector", "processor", "analyzer", "api")
foreach ($service in $services) {
    $reqFile = "services/$service/requirements.txt"
    if (Test-Path $reqFile) {
        Write-Host "  → $service" -ForegroundColor Gray
        pip install -q -r $reqFile
    }
}

Write-Host "✓ Dependencias instaladas" -ForegroundColor Green

# Descargar datos de NLTK (necesario para processor)
Write-Host "`nDescargando datos de NLTK..." -ForegroundColor Yellow
python -c "import nltk; nltk.download('vader_lexicon', quiet=True); nltk.download('punkt', quiet=True)"

Write-Host "`n" + "="*60 -ForegroundColor Cyan
Write-Host "IMPORTANTE: Este modo usa SQLite en lugar de PostgreSQL" -ForegroundColor Yellow
Write-Host "Las APIs externas (GDELT y Yahoo Finance) funcionan igual" -ForegroundColor Yellow
Write-Host "="*60 + "`n" -ForegroundColor Cyan

Write-Host "Para ejecutar el proyecto:" -ForegroundColor Cyan
Write-Host "  1. Terminal 1: python services/api/main.py" -ForegroundColor White
Write-Host "  2. Terminal 2: python services/collector/main.py" -ForegroundColor White
Write-Host "  3. Terminal 3: python services/processor/main.py" -ForegroundColor White
Write-Host "  4. Terminal 4: python services/analyzer/main.py" -ForegroundColor White

Write-Host "`n🌐 Dashboard estará en http://localhost:8000" -ForegroundColor Green
Write-Host "`nPresiona Ctrl+C en cada terminal para detener" -ForegroundColor Gray
