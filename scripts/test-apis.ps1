# Script para conectarse y probar GDELT API
# Útil para verificar que la fuente de datos funciona

Write-Host "📡 Probando conexión con GDELT API..." -ForegroundColor Cyan

# URL de ejemplo de GDELT
$gdeltUrl = "https://api.gdeltproject.org/api/v2/doc/doc?query=colombia%20economia&mode=artlist&maxrecords=10&format=json"

Write-Host "`n🔍 Consultando GDELT..." -ForegroundColor Yellow
Write-Host "Query: colombia economia (últimos 10 artículos)`n" -ForegroundColor Gray

try {
    $response = Invoke-RestMethod -Uri $gdeltUrl -Method Get -TimeoutSec 30
    
    if ($response.articles) {
        Write-Host "✅ Conexión exitosa! Se encontraron $($response.articles.Count) artículos`n" -ForegroundColor Green
        
        Write-Host "📰 Primeros 5 artículos:" -ForegroundColor Cyan
        $response.articles | Select-Object -First 5 | ForEach-Object {
            Write-Host "`n  Título: $($_.title)" -ForegroundColor White
            Write-Host "  Fuente: $($_.domain)" -ForegroundColor Gray
            Write-Host "  URL: $($_.url)" -ForegroundColor Blue
        }
    } else {
        Write-Host "⚠️ No se encontraron artículos" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Error conectando a GDELT:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

Write-Host "`n📊 Probando Yahoo Finance para COLCAP..." -ForegroundColor Cyan

# Nota: Requiere Python con yfinance instalado
$pythonTest = @"
import yfinance as yf
from datetime import datetime, timedelta

print('Obteniendo datos del COLCAP...')
colcap = yf.Ticker('^COLCAP')

end_date = datetime.now()
start_date = end_date - timedelta(days=7)

df = colcap.history(start=start_date, end=end_date)

if not df.empty:
    print(f'\n✅ Datos obtenidos: {len(df)} días')
    print('\nÚltimos 3 días:')
    print(df[['Close', 'Volume']].tail(3))
else:
    print('❌ No se obtuvieron datos')
"@

Write-Host "`n🐍 Ejecutando prueba de Python (requiere yfinance instalado)..." -ForegroundColor Yellow

try {
    $pythonTest | python -
} catch {
    Write-Host "⚠️ Python o yfinance no disponible. Instalar con:" -ForegroundColor Yellow
    Write-Host "  pip install yfinance" -ForegroundColor White
}

Write-Host "`n✅ Pruebas completadas!" -ForegroundColor Green
