$pythonExe = "C:/Users/USUARIO/OneDrive/Documentos/Semestre 6/Infraestr/Proyecto final/.venv/Scripts/python.exe"

Write-Host "Ejecutando analyzer con datos REALES del COLCAP (GXG)..." -ForegroundColor Cyan
& $pythonExe 3_run_analyzer.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nOK - Datos del COLCAP obtenidos correctamente" -ForegroundColor Green
    Write-Host "Ahora recarga el dashboard en tu navegador" -ForegroundColor Yellow
} else {
    Write-Host "`nError al ejecutar analyzer" -ForegroundColor Red
}
