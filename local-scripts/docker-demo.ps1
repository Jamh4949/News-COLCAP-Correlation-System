#!/usr/bin/env pwsh
# Script para demostrar el pipeline completo en Docker

Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "   PIPELINE NEWS-COLCAP - Ejecución con Docker        " -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar que Docker está corriendo
Write-Host "📋 Paso 1: Verificando servicios Docker..." -ForegroundColor Yellow
docker ps --format "table {{.Names}}\t{{.Status}}" | Select-String -Pattern "news-"

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# 2. Mostrar base de datos
Write-Host "📊 Paso 2: Estado de la Base de Datos" -ForegroundColor Yellow
Write-Host ""
Write-Host "Artículos en BD:" -ForegroundColor Green
docker exec news-postgres psql -U newsuser -d news_colcap -c "SELECT COUNT(*) as total_articulos FROM news;"

Write-Host ""
Write-Host "Artículos procesados:" -ForegroundColor Green
docker exec news-postgres psql -U newsuser -d news_colcap -c "SELECT sentiment_label, COUNT(*) FROM news WHERE sentiment_score IS NOT NULL GROUP BY sentiment_label;"

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# 3. Ver logs del Collector
Write-Host "📰 Paso 3: Logs del COLLECTOR (últimas 20 líneas)" -ForegroundColor Yellow
docker logs news-collector --tail 20
Write-Host ""

# 4. Ver logs del Processor
Write-Host "⚙️  Paso 4: Logs del PROCESSOR (últimas 20 líneas)" -ForegroundColor Yellow
docker logs proyectofinal-processor-1 --tail 20
Write-Host ""

# 5. Ver logs del Analyzer
Write-Host "📈 Paso 5: Logs del ANALYZER (últimas 20 líneas)" -ForegroundColor Yellow
docker logs news-analyzer --tail 20
Write-Host ""

Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# 6. Verificar API
Write-Host "🌐 Paso 6: Verificando API Dashboard" -ForegroundColor Yellow
Write-Host ""
Write-Host "Dashboard disponible en: http://localhost:8000" -ForegroundColor Green
Write-Host ""

# 7. Estadísticas del sistema
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "   ESTADÍSTICAS DEL SISTEMA                           " -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

try {
    $stats = Invoke-RestMethod -Uri "http://localhost:8000/api/stats" -Method Get
    Write-Host "📊 Total de noticias: $($stats.total_news)" -ForegroundColor Green
    Write-Host "✅ Positivas: $($stats.positive_news)" -ForegroundColor Green
    Write-Host "❌ Negativas: $($stats.negative_news)" -ForegroundColor Red
    Write-Host "⚪ Neutrales: $($stats.neutral_news)" -ForegroundColor Gray
    Write-Host "📈 Sentimiento promedio: $([math]::Round($stats.avg_sentiment, 3))" -ForegroundColor Cyan
} catch {
    Write-Host "⚠️  No se pudo obtener estadísticas de la API" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "   COMANDOS ÚTILES                                     " -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "Ver logs en tiempo real:" -ForegroundColor Yellow
Write-Host "  docker-compose logs -f" -ForegroundColor White
Write-Host ""
Write-Host "Reiniciar collector (forzar nueva recolección):" -ForegroundColor Yellow
Write-Host "  docker restart news-collector" -ForegroundColor White
Write-Host ""
Write-Host "Ver base de datos:" -ForegroundColor Yellow
Write-Host "  docker exec -it news-postgres psql -U newsuser -d news_colcap" -ForegroundColor White
Write-Host ""
Write-Host "Detener todos los servicios:" -ForegroundColor Yellow
Write-Host "  docker-compose down" -ForegroundColor White
Write-Host ""
