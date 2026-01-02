"""
API and Dashboard Service
Proporciona endpoints REST y dashboard web
Con métricas Prometheus para observabilidad
"""

import os
import json
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import redis
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============= MÉTRICAS PROMETHEUS =============
# Contadores y gauges para métricas del sistema
class PrometheusMetrics:
    """Clase para manejar métricas en formato Prometheus"""
    def __init__(self):
        self.request_count = 0
        self.request_latency_sum = 0.0
        self.last_collection_time = None
        self.last_processing_time = None
        self.last_analysis_time = None
    
    def increment_requests(self):
        self.request_count += 1
    
    def add_latency(self, latency: float):
        self.request_latency_sum += latency

metrics = PrometheusMetrics()

# Inicializar FastAPI
app = FastAPI(
    title="News-COLCAP Correlation API",
    description="API para análisis de correlación entre noticias y el índice COLCAP",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración de Redis
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    decode_responses=True
)

# Configuración de PostgreSQL
db_config = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'database': os.getenv('POSTGRES_DB', 'news_colcap'),
    'user': os.getenv('POSTGRES_USER', 'newsuser'),
    'password': os.getenv('POSTGRES_PASSWORD', 'newspass123')
}


def get_db():
    """Obtener conexión a la base de datos"""
    return psycopg2.connect(**db_config)


# Modelos Pydantic
class NewsArticle(BaseModel):
    id: int
    title: str
    url: str
    source: str
    published_date: datetime
    sentiment_score: Optional[float]
    sentiment_label: Optional[str]
    categories: Optional[List[str]]


class COLCAPData(BaseModel):
    date: str
    close_price: float
    daily_change: float
    volume: int


class CorrelationData(BaseModel):
    date: str
    news_count: int
    avg_sentiment: float
    colcap_change: float
    correlation_coefficient: float


# ============= ENDPOINTS =============

@app.get("/", response_class=HTMLResponse)
async def root():
    """Dashboard HTML principal"""
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>News-COLCAP Correlation Dashboard</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-100">
        <div class="container mx-auto px-4 py-8">
            <h1 class="text-4xl font-bold text-center mb-8 text-blue-600">
                📊 News-COLCAP Correlation System
            </h1>
            
            <!-- Stats Cards -->
            <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                <div class="bg-white rounded-lg shadow p-6">
                    <h3 class="text-gray-500 text-sm font-semibold">Total Noticias</h3>
                    <p id="total-news" class="text-3xl font-bold text-blue-600">-</p>
                </div>
                <div class="bg-white rounded-lg shadow p-6">
                    <h3 class="text-gray-500 text-sm font-semibold">Sentimiento Promedio</h3>
                    <p id="avg-sentiment" class="text-3xl font-bold text-green-600">-</p>
                </div>
                <div class="bg-white rounded-lg shadow p-6">
                    <h3 class="text-gray-500 text-sm font-semibold">COLCAP Cambio</h3>
                    <p id="colcap-change" class="text-3xl font-bold text-purple-600">-</p>
                </div>
                <div class="bg-white rounded-lg shadow p-6">
                    <h3 class="text-gray-500 text-sm font-semibold">Correlación</h3>
                    <p id="correlation" class="text-3xl font-bold text-orange-600">-</p>
                </div>
            </div>
            
            <!-- Charts - 3 Gráficas principales -->
            <div class="grid grid-cols-1 gap-6 mb-8">
                <!-- Gráfica 1: Solo COLCAP -->
                <div class="bg-white rounded-lg shadow p-6">
                    <h2 class="text-xl font-semibold mb-4">📈 Índice COLCAP - Últimos 90 días</h2>
                    <canvas id="colcapChart"></canvas>
                </div>
                
                <!-- Gráfica 2: Solo Sentimiento -->
                <div class="bg-white rounded-lg shadow p-6">
                    <h2 class="text-xl font-semibold mb-4">💭 Sentimiento de Noticias - Últimos 90 días</h2>
                    <canvas id="sentimentLineChart"></canvas>
                </div>
                
                <!-- Gráfica 3: Sentimiento vs COLCAP (Comparación) -->
                <div class="bg-white rounded-lg shadow p-6">
                    <h2 class="text-xl font-semibold mb-4">🔄 Comparación: Sentimiento vs COLCAP</h2>
                    <canvas id="correlationChart"></canvas>
                </div>
            </div>
            
            <!-- Distribución de Sentimiento -->
            <div class="bg-white rounded-lg shadow p-6 mb-8">
                <h2 class="text-xl font-semibold mb-4">📊 Distribución de Sentimiento</h2>
                <div class="max-w-md mx-auto">
                    <canvas id="sentimentChart"></canvas>
                </div>
            </div>
            
            <!-- Conclusiones del Análisis -->
            <div class="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg shadow-lg p-6 mb-8">
                <h2 class="text-2xl font-bold mb-4 text-blue-800">💡 Conclusiones del Análisis</h2>
                <div id="conclusiones-container">
                    <p class="text-gray-500">Cargando conclusiones...</p>
                </div>
            </div>
            
            <!-- Recent News -->
            <div class="bg-white rounded-lg shadow p-6">
                <h2 class="text-xl font-semibold mb-4">Noticias Recientes</h2>
                <div id="recent-news" class="space-y-4">
                    <p class="text-gray-500">Cargando...</p>
                </div>
            </div>
        </div>
        
        <script>
            // Cargar datos al iniciar
            async function loadDashboard() {
                try {
                    // Cargar estadísticas
                    const stats = await fetch('/api/stats').then(r => r.json());
                    document.getElementById('total-news').textContent = stats.total_news.toLocaleString();
                    document.getElementById('avg-sentiment').textContent = stats.avg_sentiment.toFixed(3);
                    document.getElementById('colcap-change').textContent = stats.latest_colcap_change.toFixed(2) + '%';
                    document.getElementById('correlation').textContent = stats.correlation.toFixed(3);
                    
                    // Cargar correlaciones (últimos 90 días o todas las disponibles)
                    const correlations = await fetch('/api/correlations?days=90').then(r => r.json());
                    drawCOLCAPChart(correlations);
                    drawSentimentLineChart(correlations);
                    drawCorrelationChart(correlations);
                    
                    // Cargar noticias recientes
                    const news = await fetch('/api/news/recent?limit=10').then(r => r.json());
                    displayRecentNews(news);
                    
                    // Cargar distribución de sentimiento
                    const sentiment = await fetch('/api/news/sentiment-distribution').then(r => r.json());
                    drawSentimentChart(sentiment);
                    
                    // Cargar conclusiones
                    const conclusiones = await fetch('/api/conclusiones').then(r => r.json());
                    displayConclusiones(conclusiones);
                    
                } catch (error) {
                    console.error('Error cargando dashboard:', error);
                }
            }
            
            function drawCOLCAPChart(data) {
                const ctx = document.getElementById('colcapChart').getContext('2d');
                
                // Invertir el orden de los datos para que las fechas antiguas estén a la izquierda
                const reversedData = [...data].reverse();
                
                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: reversedData.map(d => d.date),
                        datasets: [{
                            label: 'COLCAP Cambio %',
                            data: reversedData.map(d => d.colcap_change),
                            borderColor: 'rgb(168, 85, 247)',
                            backgroundColor: 'rgba(168, 85, 247, 0.1)',
                            fill: true
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: {
                                title: { display: true, text: 'Cambio Porcentual (%)' }
                            }
                        }
                    }
                });
            }
            
            function drawSentimentLineChart(data) {
                const ctx = document.getElementById('sentimentLineChart').getContext('2d');
                
                // Invertir el orden de los datos para que las fechas antiguas estén a la izquierda
                const reversedData = [...data].reverse();
                
                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: reversedData.map(d => d.date),
                        datasets: [{
                            label: 'Sentimiento Promedio',
                            data: reversedData.map(d => d.avg_sentiment),
                            borderColor: 'rgb(59, 130, 246)',
                            backgroundColor: 'rgba(59, 130, 246, 0.1)',
                            fill: true
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: {
                                title: { display: true, text: 'Sentimiento' },
                                min: -0.3,
                                max: 1.0
                            }
                        }
                    }
                });
            }
            
            function drawCorrelationChart(data) {
                const ctx = document.getElementById('correlationChart').getContext('2d');
                
                // Invertir el orden de los datos para que las fechas antiguas estén a la izquierda
                const reversedData = [...data].reverse();
                
                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: reversedData.map(d => d.date),
                        datasets: [
                            {
                                label: 'Sentimiento Promedio',
                                data: reversedData.map(d => d.avg_sentiment),
                                borderColor: 'rgb(59, 130, 246)',
                                yAxisID: 'y'
                            },
                            {
                                label: 'COLCAP Cambio %',
                                data: reversedData.map(d => d.colcap_change),
                                borderColor: 'rgb(168, 85, 247)',
                                yAxisID: 'y1'
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: {
                                type: 'linear',
                                position: 'left',
                                title: { display: true, text: 'Sentimiento' },
                                min: -0.3,
                                max: 1.0
                            },
                            y1: {
                                type: 'linear',
                                position: 'right',
                                title: { display: true, text: 'COLCAP %' },
                                grid: { drawOnChartArea: false }
                            }
                        }
                    }
                });
            }
            
            function drawSentimentChart(data) {
                const ctx = document.getElementById('sentimentChart').getContext('2d');
                new Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        labels: ['Positivo', 'Neutral', 'Negativo'],
                        datasets: [{
                            data: [data.positive, data.neutral, data.negative],
                            backgroundColor: ['#10b981', '#6b7280', '#ef4444']
                        }]
                    },
                    options: { responsive: true }
                });
            }
            
            function displayRecentNews(news) {
                const container = document.getElementById('recent-news');
                container.innerHTML = news.map(article => `
                    <div class="border-l-4 ${getSentimentColor(article.sentiment_label)} pl-4 py-2">
                        <h3 class="font-semibold">${article.title}</h3>
                        <p class="text-sm text-gray-600">
                            ${article.source} - ${new Date(article.published_date).toLocaleDateString()}
                            - Sentimiento: ${article.sentiment_label} (${article.sentiment_score.toFixed(2)})
                        </p>
                    </div>
                `).join('');
            }
            
            function getSentimentColor(label) {
                return {
                    'positive': 'border-green-500',
                    'neutral': 'border-gray-500',
                    'negative': 'border-red-500'
                }[label] || 'border-gray-300';
            }
            
            function displayConclusiones(data) {
                const container = document.getElementById('conclusiones-container');
                
                // Determinar colores según tendencias
                const sentimentColor = data.sentimiento.tono === 'POSITIVO' ? 'text-green-600' : 
                                      data.sentimiento.tono === 'NEGATIVO' ? 'text-red-600' : 'text-gray-600';
                const colcapColor = data.colcap.tendencia === 'ALCISTA' ? 'text-green-600' : 
                                   data.colcap.tendencia === 'BAJISTA' ? 'text-red-600' : 'text-gray-600';
                
                container.innerHTML = `
                    <!-- Resumen General -->
                    <div class="bg-white rounded-lg p-4 mb-4 shadow-sm">
                        <h3 class="font-bold text-lg mb-2">📊 Resumen General</h3>
                        <p class="text-gray-700">${data.resumen}</p>
                    </div>
                    
                    <!-- Análisis en dos columnas -->
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                        <!-- Sentimiento -->
                        <div class="bg-white rounded-lg p-4 shadow-sm">
                            <h3 class="font-bold text-lg mb-2">💭 Análisis de Sentimiento</h3>
                            <div class="space-y-2">
                                <p><span class="font-semibold ${sentimentColor}">${data.sentimiento.tono}</span> 
                                   (Score: ${data.sentimiento.score})</p>
                                <p class="text-sm text-gray-600">${data.sentimiento.descripcion}</p>
                                <p class="text-sm">Volatilidad: <span class="font-semibold">${data.sentimiento.volatilidad}</span></p>
                            </div>
                        </div>
                        
                        <!-- COLCAP -->
                        <div class="bg-white rounded-lg p-4 shadow-sm">
                            <h3 class="font-bold text-lg mb-2">📈 Análisis COLCAP</h3>
                            <div class="space-y-2">
                                <p><span class="font-semibold ${colcapColor}">${data.colcap.tendencia}</span> 
                                   (${data.colcap.cambio_promedio > 0 ? '+' : ''}${data.colcap.cambio_promedio}%)</p>
                                <p class="text-sm text-gray-600">${data.colcap.descripcion}</p>
                                <p class="text-sm">Volatilidad: <span class="font-semibold">${data.colcap.volatilidad}%</span></p>
                                <p class="text-sm text-gray-500">${data.colcap.dias_analizados} días analizados</p>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Interpretación -->
                    <div class="bg-white rounded-lg p-4 shadow-sm">
                        <h3 class="font-bold text-lg mb-2">🔍 Interpretación</h3>
                        <ul class="space-y-1">
                            ${data.interpretacion.map(item => `<li class="text-gray-700">${item}</li>`).join('')}
                        </ul>
                    </div>
                `;
            }
            
            // Cargar dashboard al iniciar
            loadDashboard();
            
            // Actualizar cada 5 minutos
            setInterval(loadDashboard, 300000);
        </script>
    </body>
    </html>
    """


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Verificar conexión a Redis
        redis_client.ping()
        redis_status = "OK"
    except:
        redis_status = "ERROR"
    
    try:
        # Verificar conexión a PostgreSQL
        conn = get_db()
        conn.close()
        db_status = "OK"
    except:
        db_status = "ERROR"
    
    return {
        "status": "healthy" if redis_status == "OK" and db_status == "OK" else "degraded",
        "redis": redis_status,
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/stats")
async def get_stats():
    """Obtener estadísticas generales del sistema"""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Total de noticias
        cursor.execute("SELECT COUNT(*) as count FROM news")
        total_news = cursor.fetchone()['count']
        
        # Sentimiento promedio
        cursor.execute("SELECT AVG(sentiment_score) as avg FROM news WHERE sentiment_score IS NOT NULL")
        avg_sentiment = cursor.fetchone()['avg'] or 0.0
        
        # Último cambio COLCAP
        cursor.execute("SELECT daily_change FROM colcap_data ORDER BY date DESC LIMIT 1")
        result = cursor.fetchone()
        latest_colcap_change = float(result['daily_change']) if result else 0.0
        
        # Correlación más reciente
        correlation_stats = redis_client.get('latest_correlation_stats')
        if correlation_stats:
            stats = json.loads(correlation_stats)
            correlation = stats.get('pearson_correlation', 0.0)
        else:
            correlation = 0.0
        
        return {
            "total_news": total_news,
            "avg_sentiment": float(avg_sentiment),
            "latest_colcap_change": latest_colcap_change,
            "correlation": correlation,
            "last_updated": datetime.utcnow().isoformat()
        }
    finally:
        cursor.close()
        conn.close()


@app.get("/api/news/recent", response_model=List[NewsArticle])
async def get_recent_news(limit: int = Query(default=20, le=100)):
    """Obtener noticias recientes"""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute("""
            SELECT id, title, url, source, published_date,
                   sentiment_score, sentiment_label, categories
            FROM news
            WHERE sentiment_score IS NOT NULL
            ORDER BY published_date DESC
            LIMIT %s
        """, (limit,))
        
        news = cursor.fetchall()
        return news
    finally:
        cursor.close()
        conn.close()


@app.get("/api/news/sentiment-distribution")
async def get_sentiment_distribution():
    """Obtener distribución de sentimientos"""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute("""
            SELECT 
                sentiment_label,
                COUNT(*) as count
            FROM news
            WHERE sentiment_label IS NOT NULL
            GROUP BY sentiment_label
        """)
        
        results = cursor.fetchall()
        
        distribution = {'positive': 0, 'neutral': 0, 'negative': 0}
        for row in results:
            distribution[row['sentiment_label']] = row['count']
        
        return distribution
    finally:
        cursor.close()
        conn.close()


@app.get("/api/colcap/latest", response_model=List[COLCAPData])
async def get_latest_colcap(days: int = Query(default=30, le=365)):
    """Obtener datos recientes del COLCAP"""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute("""
            SELECT date, close_price, daily_change, volume
            FROM colcap_data
            ORDER BY date DESC
            LIMIT %s
        """, (days,))
        
        data = cursor.fetchall()
        return [
            {
                'date': str(row['date']),
                'close_price': float(row['close_price']),
                'daily_change': float(row['daily_change']),
                'volume': row['volume']
            }
            for row in data
        ]
    finally:
        cursor.close()
        conn.close()


@app.get("/api/correlations", response_model=List[CorrelationData])
async def get_correlations(days: int = Query(default=365, le=365)):
    """Obtener datos de correlación (último año completo)"""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute("""
            SELECT date, news_count, avg_sentiment, 
                   colcap_change, correlation_coefficient
            FROM correlations
            ORDER BY date DESC
            LIMIT %s
        """, (days,))
        
        data = cursor.fetchall()
        return [
            {
                'date': str(row['date']),
                'news_count': row['news_count'],
                'avg_sentiment': float(row['avg_sentiment']),
                'colcap_change': float(row['colcap_change']),
                'correlation_coefficient': float(row['correlation_coefficient'])
            }
            for row in data
        ]
    finally:
        cursor.close()
        conn.close()


@app.get("/api/news/search")
async def search_news(
    query: str = Query(..., min_length=3),
    limit: int = Query(default=20, le=100)
):
    """Buscar noticias por texto"""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute("""
            SELECT id, title, url, source, published_date,
                   sentiment_score, sentiment_label
            FROM news
            WHERE title ILIKE %s OR content ILIKE %s
            ORDER BY published_date DESC
            LIMIT %s
        """, (f'%{query}%', f'%{query}%', limit))
        
        results = cursor.fetchall()
        return results
    finally:
        cursor.close()
        conn.close()


@app.get("/api/metrics")
async def get_metrics():
    """Métricas del sistema para monitoreo"""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Noticias procesadas hoy
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM news
            WHERE DATE(created_at) = CURRENT_DATE
        """)
        news_today = cursor.fetchone()['count']
        
        # Noticias pendientes de procesar
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM news
            WHERE sentiment_score IS NULL
        """)
        pending = cursor.fetchone()['count']
        
        return {
            "news_collected_today": news_today,
            "news_pending_processing": pending,
            "redis_connected": redis_client.ping(),
            "timestamp": datetime.utcnow().isoformat()
        }
    finally:
        cursor.close()
        conn.close()


@app.get("/metrics", response_class=PlainTextResponse)
async def prometheus_metrics():
    """
    Endpoint de métricas en formato Prometheus
    Expone métricas para scraping por Prometheus
    """
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Total de noticias
        cursor.execute("SELECT COUNT(*) as total FROM news")
        total_news = cursor.fetchone()['total']
        
        # Noticias procesadas (con sentimiento)
        cursor.execute("SELECT COUNT(*) as total FROM news WHERE sentiment_score IS NOT NULL")
        processed_news = cursor.fetchone()['total']
        
        # Noticias pendientes
        pending_news = total_news - processed_news
        
        # Distribución de sentimiento
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN sentiment_label = 'positive' THEN 1 END) as positive,
                COUNT(CASE WHEN sentiment_label = 'negative' THEN 1 END) as negative,
                COUNT(CASE WHEN sentiment_label = 'neutral' THEN 1 END) as neutral
            FROM news WHERE sentiment_label IS NOT NULL
        """)
        sentiment = cursor.fetchone()
        
        # Datos COLCAP
        cursor.execute("SELECT COUNT(*) as total FROM colcap_data")
        colcap_days = cursor.fetchone()['total']
        
        # Correlaciones
        cursor.execute("SELECT COUNT(*) as total FROM correlations")
        correlations = cursor.fetchone()['total']
        
        # Último precio COLCAP
        cursor.execute("SELECT close_price, daily_change FROM colcap_data ORDER BY date DESC LIMIT 1")
        colcap_latest = cursor.fetchone()
        
        # Sentimiento promedio
        cursor.execute("SELECT AVG(sentiment_score) as avg FROM news WHERE sentiment_score IS NOT NULL")
        avg_sentiment = cursor.fetchone()['avg'] or 0.0
        
        # Verificar Redis
        try:
            redis_client.ping()
            redis_up = 1
        except:
            redis_up = 0
        
        # Generar métricas en formato Prometheus
        prometheus_output = f"""# HELP news_colcap_news_total Total number of news articles collected
# TYPE news_colcap_news_total gauge
news_colcap_news_total {total_news}

# HELP news_colcap_news_processed Number of news articles with sentiment analysis
# TYPE news_colcap_news_processed gauge
news_colcap_news_processed {processed_news}

# HELP news_colcap_news_pending Number of news articles pending processing
# TYPE news_colcap_news_pending gauge
news_colcap_news_pending {pending_news}

# HELP news_colcap_sentiment_positive Number of positive sentiment articles
# TYPE news_colcap_sentiment_positive gauge
news_colcap_sentiment_positive {sentiment['positive'] or 0}

# HELP news_colcap_sentiment_negative Number of negative sentiment articles
# TYPE news_colcap_sentiment_negative gauge
news_colcap_sentiment_negative {sentiment['negative'] or 0}

# HELP news_colcap_sentiment_neutral Number of neutral sentiment articles
# TYPE news_colcap_sentiment_neutral gauge
news_colcap_sentiment_neutral {sentiment['neutral'] or 0}

# HELP news_colcap_sentiment_average Average sentiment score
# TYPE news_colcap_sentiment_average gauge
news_colcap_sentiment_average {float(avg_sentiment):.4f}

# HELP news_colcap_colcap_days Total days of COLCAP data
# TYPE news_colcap_colcap_days gauge
news_colcap_colcap_days {colcap_days}

# HELP news_colcap_correlations_total Total correlation records
# TYPE news_colcap_correlations_total gauge
news_colcap_correlations_total {correlations}

# HELP news_colcap_colcap_price Latest COLCAP closing price
# TYPE news_colcap_colcap_price gauge
news_colcap_colcap_price {float(colcap_latest['close_price']) if colcap_latest else 0}

# HELP news_colcap_colcap_change Latest COLCAP daily change percentage
# TYPE news_colcap_colcap_change gauge
news_colcap_colcap_change {float(colcap_latest['daily_change']) if colcap_latest else 0}

# HELP news_colcap_redis_up Redis connection status (1=up, 0=down)
# TYPE news_colcap_redis_up gauge
news_colcap_redis_up {redis_up}

# HELP news_colcap_api_requests_total Total API requests (approximate)
# TYPE news_colcap_api_requests_total counter
news_colcap_api_requests_total {metrics.request_count}

# HELP news_colcap_info System information
# TYPE news_colcap_info gauge
news_colcap_info{{version="1.0.0",service="api"}} 1
"""
        
        metrics.increment_requests()
        return prometheus_output
        
    finally:
        cursor.close()
        conn.close()


@app.get("/api/conclusiones")
async def get_conclusiones():
    """Generar conclusiones automáticas del análisis"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Estadísticas de noticias
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN sentiment_label = 'positive' THEN 1 END) as positivas,
                COUNT(CASE WHEN sentiment_label = 'negative' THEN 1 END) as negativas,
                COUNT(CASE WHEN sentiment_label = 'neutral' THEN 1 END) as neutrales,
                AVG(sentiment_score) as promedio_sent,
                STDDEV(sentiment_score) as volatilidad_sent
            FROM news
            WHERE sentiment_score IS NOT NULL
        """)
        
        news_stats = cursor.fetchone()
        total, positivas, negativas, neutrales, avg_sent, std_sent = news_stats
        
        # Estadísticas COLCAP
        cursor.execute("""
            SELECT 
                AVG(daily_change) as promedio_cambio,
                STDDEV(daily_change) as volatilidad,
                MAX(daily_change) as max_cambio,
                MIN(daily_change) as min_cambio,
                MAX(close_price) as max_precio,
                MIN(close_price) as min_precio,
                COUNT(*) as dias_datos
            FROM colcap_data
            WHERE date >= CURRENT_DATE - INTERVAL '30 days'
        """)
        
        colcap_stats = cursor.fetchone()
        avg_change, volatilidad, max_change, min_change, max_price, min_price, dias_datos = colcap_stats
        
        # Generar conclusiones
        pct_pos = (positivas / total * 100) if total > 0 else 0
        pct_neg = (negativas / total * 100) if total > 0 else 0
        pct_neu = (neutrales / total * 100) if total > 0 else 0
        
        avg_sent_val = float(avg_sent) if avg_sent else 0.0
        avg_change_val = float(avg_change) if avg_change else 0.0
        
        # Determinar tono de sentimiento
        if avg_sent_val < -0.1:
            tono_sentimiento = "NEGATIVO"
            desc_sentimiento = "Las noticias reflejan preocupación en el mercado"
        elif avg_sent_val > 0.1:
            tono_sentimiento = "POSITIVO"
            desc_sentimiento = "Las noticias reflejan optimismo en el mercado"
        else:
            tono_sentimiento = "NEUTRAL"
            desc_sentimiento = "Las noticias reflejan estabilidad en el mercado"
        
        # Determinar tendencia COLCAP
        if avg_change_val > 0.5:
            tendencia_colcap = "ALCISTA"
            desc_colcap = "El índice muestra tendencia positiva"
        elif avg_change_val < -0.5:
            tendencia_colcap = "BAJISTA"
            desc_colcap = "El índice muestra tendencia negativa"
        else:
            tendencia_colcap = "LATERAL"
            desc_colcap = "El índice se mantiene estable"
        
        # Interpretación
        interpretacion = []
        if avg_sent_val < -0.05 and avg_change_val < 0:
            interpretacion.append("✓ COHERENCIA: Sentimiento negativo coincide con caída del COLCAP")
        elif avg_sent_val > 0.05 and avg_change_val > 0:
            interpretacion.append("✓ COHERENCIA: Sentimiento positivo coincide con alza del COLCAP")
        elif abs(avg_sent_val) < 0.05 and abs(avg_change_val) < 0.5:
            interpretacion.append("✓ EQUILIBRIO: Mercado estable sin señales fuertes")
        
        if pct_neg > 30:
            interpretacion.append(f"⚠ ALERTA: Alto porcentaje de noticias negativas ({pct_neg:.1f}%)")
        
        return {
            "resumen": f"Análisis de {total} noticias: {pct_pos:.1f}% positivas, {pct_neg:.1f}% negativas, {pct_neu:.1f}% neutrales",
            "sentimiento": {
                "tono": tono_sentimiento,
                "descripcion": desc_sentimiento,
                "score": round(avg_sent_val, 3),
                "volatilidad": round(float(std_sent) if std_sent else 0.0, 3)
            },
            "colcap": {
                "tendencia": tendencia_colcap,
                "descripcion": desc_colcap,
                "cambio_promedio": round(avg_change_val, 2),
                "volatilidad": round(float(volatilidad) if volatilidad else 0.0, 2),
                "dias_analizados": dias_datos
            },
            "interpretacion": interpretacion,
            "metricas": {
                "noticias_total": total,
                "positivas": positivas,
                "negativas": negativas,
                "neutrales": neutrales
            }
        }
        
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
