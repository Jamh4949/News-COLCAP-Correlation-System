# Pipeline completo de análisis de noticias
Write-Host "="*70 -ForegroundColor Cyan
Write-Host "PIPELINE COMPLETO: News-COLCAP Analyzer" -ForegroundColor Cyan
Write-Host "="*70 -ForegroundColor Cyan

$pythonExe = "C:/Users/USUARIO/OneDrive/Documentos/Semestre 6/Infraestr/Proyecto final/.venv/Scripts/python.exe"

# Paso 1: Collector
Write-Host "`n[1/4] COLLECTOR - Obteniendo noticias de GDELT..." -ForegroundColor Yellow
& $pythonExe 1_run_collector.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error en Collector" -ForegroundColor Red
    exit 1
}

Write-Host "`nPresiona Enter para continuar al Processor..." -ForegroundColor Gray
Read-Host

# Paso 2: Processor
Write-Host "`n[2/4] PROCESSOR - Analizando sentimientos..." -ForegroundColor Yellow
& $pythonExe 2_run_processor.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error en Processor" -ForegroundColor Red
    exit 1
}

Write-Host "`nPresiona Enter para continuar al Analyzer..." -ForegroundColor Gray
Read-Host

# Paso 3: Analyzer
Write-Host "`n[3/4] ANALYZER - Obteniendo datos COLCAP..." -ForegroundColor Yellow
& $pythonExe 3_run_analyzer.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error en Analyzer" -ForegroundColor Red
    exit 1
}

Write-Host "`nPresiona Enter para iniciar Dashboard..." -ForegroundColor Gray
Read-Host

# Paso 4: Dashboard
Write-Host "`n[4/4] DASHBOARD - Iniciando servidor web..." -ForegroundColor Yellow
Write-Host "`nAccede a: http://localhost:8000" -ForegroundColor Green
Write-Host "Presiona Ctrl+C para detener el servidor`n" -ForegroundColor Gray
& $pythonExe 4_run_dashboard.py
