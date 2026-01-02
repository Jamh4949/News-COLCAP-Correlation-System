"""
API and Dashboard Service
Proporciona endpoints REST y dashboard web
Con métricas Prometheus para observabilidad
"""

import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import psycopg2
import redis
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.concurrency import run_in_threadpool  # ✅ FIX
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool  # ✅ FIX
from pydantic import BaseModel

# ================= LOGGING =================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================= FASTAPI =================
app = FastAPI(
    title="News-COLCAP Correlation API",
    description="API para análisis de correlación entre noticias y el índice COLCAP",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= REDIS =================
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True,
)

# ================= POSTGRES =================
db_config = {
    "host": os.getenv("POSTGRES_HOST"),
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "port": 5432,
}

# ✅ FIX: pool global
db_pool: Optional[SimpleConnectionPool] = None


# ✅ FIX: inicialización con retry (Swarm-safe)
@app.on_event("startup")
def startup():
    global db_pool
    for i in range(10):
        try:
            db_pool = SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                **db_config,
            )
            logger.info("✅ PostgreSQL pool inicializado")
            return
        except Exception as e:
            logger.warning(f"Postgres no disponible ({i + 1}/10): {e}")
            time.sleep(3)

    raise RuntimeError("PostgreSQL no disponible")


# ✅ FIX: helper único para DB
def run_db(fn):
    conn = db_pool.getconn()
    try:
        return fn(conn)
    finally:
        db_pool.putconn(conn)


# ================= MODELOS =================
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


# ================= DASHBOARD =================
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

        <!-- Charts -->
        <div class="grid grid-cols-1 gap-6 mb-8">
            <div class="bg-white rounded-lg shadow p-6">
                <h2 class="text-xl font-semibold mb-4">📈 Índice COLCAP - Últimos 90 días</h2>
                <canvas id="colcapChart"></canvas>
            </div>

            <div class="bg-white rounded-lg shadow p-6">
                <h2 class="text-xl font-semibold mb-4">💭 Sentimiento de Noticias - Últimos 90 días</h2>
                <canvas id="sentimentLineChart"></canvas>
            </div>

            <div class="bg-white rounded-lg shadow p-6">
                <h2 class="text-xl font-semibold mb-4">🔄 Comparación: Sentimiento vs COLCAP</h2>
                <canvas id="correlationChart"></canvas>
            </div>
        </div>

        <div class="bg-white rounded-lg shadow p-6 mb-8">
            <h2 class="text-xl font-semibold mb-4">📊 Distribución de Sentimiento</h2>
            <div class="max-w-md mx-auto">
                <canvas id="sentimentChart"></canvas>
            </div>
        </div>

        <div class="bg-white rounded-lg shadow p-6">
            <h2 class="text-xl font-semibold mb-4">Noticias Recientes</h2>
            <div id="recent-news" class="space-y-4">
                <p class="text-gray-500">Cargando...</p>
            </div>
        </div>
    </div>

<script>
async function loadDashboard() {
    const stats = await fetch('/api/stats').then(r => r.json());
    document.getElementById('total-news').textContent = stats.total_news;
    document.getElementById('avg-sentiment').textContent = stats.avg_sentiment.toFixed(3);
    document.getElementById('colcap-change').textContent = stats.latest_colcap_change.toFixed(2) + '%';
    document.getElementById('correlation').textContent = stats.correlation.toFixed(3);

    const correlations = await fetch('/api/correlations?days=90').then(r => r.json());
    const reversed = [...correlations].reverse();

    new Chart(document.getElementById('colcapChart'), {
        type: 'line',
        data: { labels: reversed.map(d => d.date),
            datasets: [{ data: reversed.map(d => d.colcap_change), label: 'COLCAP %' }]
        }
    });

    new Chart(document.getElementById('sentimentLineChart'), {
        type: 'line',
        data: { labels: reversed.map(d => d.date),
            datasets: [{ data: reversed.map(d => d.avg_sentiment), label: 'Sentimiento' }]
        }
    });

    new Chart(document.getElementById('correlationChart'), {
        type: 'line',
        data: {
            labels: reversed.map(d => d.date),
            datasets: [
                { data: reversed.map(d => d.avg_sentiment), label: 'Sentimiento' },
                { data: reversed.map(d => d.colcap_change), label: 'COLCAP %' }
            ]
        }
    });

    const news = await fetch('/api/news/recent?limit=10').then(r => r.json());
    document.getElementById('recent-news').innerHTML = news.map(n =>
        `<div><strong>${n.title}</strong><br>${n.source}</div>`
    ).join('');
}

loadDashboard();
</script>
</body>
</html>
    """


# ================= HEALTH =================
@app.get("/api/health")
async def health_check():
    def _check(conn):
        conn.cursor().execute("SELECT 1")
        return True

    db_ok = await run_in_threadpool(lambda: run_db(_check))
    redis_ok = redis_client.ping()

    return {
        "status": "healthy" if db_ok and redis_ok else "degraded",
        "redis": "OK" if redis_ok else "ERROR",
        "database": "OK" if db_ok else "ERROR",
        "timestamp": datetime.utcnow().isoformat(),
    }


# ================= STATS =================
def _get_stats(conn):
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("SELECT COUNT(*) as count FROM news")
    total_news = cursor.fetchone()["count"]

    cursor.execute(
        "SELECT AVG(sentiment_score) as avg FROM news WHERE sentiment_score IS NOT NULL"
    )
    avg_sentiment = cursor.fetchone()["avg"] or 0.0

    cursor.execute("SELECT daily_change FROM colcap_data ORDER BY date DESC LIMIT 1")
    row = cursor.fetchone()
    latest_colcap_change = float(row["daily_change"]) if row else 0.0

    correlation_stats = redis_client.get("latest_correlation_stats")
    correlation = (
        json.loads(correlation_stats).get("pearson_correlation", 0.0)
        if correlation_stats
        else 0.0
    )

    return {
        "total_news": total_news,
        "avg_sentiment": float(avg_sentiment),
        "latest_colcap_change": latest_colcap_change,
        "correlation": correlation,
        "last_updated": datetime.utcnow().isoformat(),
    }


@app.get("/api/stats")
async def get_stats():
    # ✅ FIX: ejecución segura en threadpool
    return await run_in_threadpool(lambda: run_db(_get_stats))


# ================= NEWS =================
def _get_recent_news(conn, limit):
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        """
        SELECT id, title, url, source, published_date,
               sentiment_score, sentiment_label, categories
        FROM news
        WHERE sentiment_score IS NOT NULL
        ORDER BY published_date DESC
        LIMIT %s
        """,
        (limit,),
    )
    return cursor.fetchall()


@app.get("/api/news/recent", response_model=List[NewsArticle])
async def get_recent_news(limit: int = Query(default=20, le=100)):
    return await run_in_threadpool(
        lambda: run_db(lambda conn: _get_recent_news(conn, limit))
    )


# ================= SENTIMENT DISTRIBUTION =================
def _get_sentiment_distribution(conn):
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        """
        SELECT sentiment_label, COUNT(*) as count
        FROM news
        WHERE sentiment_label IS NOT NULL
        GROUP BY sentiment_label
        """
    )

    rows = cursor.fetchall()
    distribution = {"positive": 0, "neutral": 0, "negative": 0}
    for r in rows:
        distribution[r["sentiment_label"]] = r["count"]

    return distribution


@app.get("/api/news/sentiment-distribution")
async def get_sentiment_distribution():
    return await run_in_threadpool(lambda: run_db(_get_sentiment_distribution))


# ================= COLCAP =================
def _get_latest_colcap(conn, days):
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        """
        SELECT date, close_price, daily_change, volume
        FROM colcap_data
        ORDER BY date DESC
        LIMIT %s
        """,
        (days,),
    )

    return [
        {
            "date": str(r["date"]),
            "close_price": float(r["close_price"]),
            "daily_change": float(r["daily_change"]),
            "volume": r["volume"],
        }
        for r in cursor.fetchall()
    ]


@app.get("/api/colcap/latest", response_model=List[COLCAPData])
async def get_latest_colcap(days: int = Query(default=30, le=365)):
    return await run_in_threadpool(
        lambda: run_db(lambda conn: _get_latest_colcap(conn, days))
    )


# ================= CORRELATIONS =================
def _get_correlations(conn, days):
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        """
        SELECT date, news_count, avg_sentiment,
               colcap_change, correlation_coefficient
        FROM correlations
        ORDER BY date DESC
        LIMIT %s
        """,
        (days,),
    )

    return [
        {
            "date": str(r["date"]),
            "news_count": r["news_count"],
            "avg_sentiment": float(r["avg_sentiment"]),
            "colcap_change": float(r["colcap_change"]),
            "correlation_coefficient": float(r["correlation_coefficient"]),
        }
        for r in cursor.fetchall()
    ]


@app.get("/api/correlations", response_model=List[CorrelationData])
async def get_correlations(days: int = Query(default=365, le=365)):
    return await run_in_threadpool(
        lambda: run_db(lambda conn: _get_correlations(conn, days))
    )


# ================= METRICS (PROMETHEUS) =================
@app.get("/metrics", response_class=PlainTextResponse)
async def prometheus_metrics():
    def _metrics(conn):
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM news")
        total_news = cursor.fetchone()[0]
        return f"news_colcap_news_total {total_news}\n"

    return await run_in_threadpool(lambda: run_db(_metrics))


# ================= CONCLUSIONES =================
def _get_conclusiones(conn):
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            COUNT(*) as total,
            AVG(sentiment_score) as avg_sent
        FROM news
        WHERE sentiment_score IS NOT NULL
        """
    )

    total, avg_sent = cursor.fetchone()
    avg_sent_val = float(avg_sent) if avg_sent else 0.0

    return {
        "resumen": f"Análisis de {total} noticias",
        "sentimiento": {
            "tono": "POSITIVO"
            if avg_sent_val > 0.1
            else "NEGATIVO"
            if avg_sent_val < -0.1
            else "NEUTRAL",
            "score": round(avg_sent_val, 3),
        },
    }


@app.get("/api/conclusiones")
async def get_conclusiones():
    return await run_in_threadpool(lambda: run_db(_get_conclusiones))


# ================= MAIN =================
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
