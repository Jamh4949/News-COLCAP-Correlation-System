"""
DEMO SIMPLIFICADA - Dashboard API
Servidor web con visualización de resultados
"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import json
import os

app = FastAPI(title="News-COLCAP Analyzer")

# Cargar datos
def load_data():
    data = {}
    try:
        with open('data/processed_news.json', 'r', encoding='utf-8') as f:
            data['news'] = json.load(f)
    except:
        data['news'] = []
    
    try:
        with open('data/colcap_data.json', 'r', encoding='utf-8') as f:
            data['colcap'] = json.load(f)
    except:
        data['colcap'] = {}
    
    return data

@app.get("/api/health")
def health():
    return {"status": "healthy", "version": "1.0-demo"}

@app.get("/api/stats")
def get_stats():
    data = load_data()
    news = data['news']
    
    if not news:
        return {"error": "No hay datos. Ejecuta 1_run_collector.py primero"}
    
    total = len(news)
    positive = len([n for n in news if n['sentiment_label'] == 'positive'])
    negative = len([n for n in news if n['sentiment_label'] == 'negative'])
    neutral = len([n for n in news if n['sentiment_label'] == 'neutral'])
    avg_sentiment = sum(n['sentiment_score'] for n in news) / total
    
    return {
        "total_news": total,
        "positive": positive,
        "negative": negative,
        "neutral": neutral,
        "avg_sentiment": round(avg_sentiment, 3),
        "positive_ratio": round(positive/total, 3),
        "negative_ratio": round(negative/total, 3)
    }

@app.get("/api/news/recent")
def get_recent_news():
    data = load_data()
    return data['news'][:20]  # Últimas 20

@app.get("/api/colcap")
def get_colcap():
    data = load_data()
    return data['colcap']

@app.get("/", response_class=HTMLResponse)
def dashboard():
    data = load_data()
    news = data['news']
    colcap = data['colcap']
    
    # Calcular stats
    if news:
        total = len(news)
        positive = len([n for n in news if n['sentiment_label'] == 'positive'])
        negative = len([n for n in news if n['sentiment_label'] == 'negative'])
        neutral = len([n for n in news if n['sentiment_label'] == 'neutral'])
        avg_sentiment = sum(n['sentiment_score'] for n in news) / total
    else:
        total = positive = negative = neutral = 0
        avg_sentiment = 0
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>News-COLCAP Analyzer</title>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }}
            .container {{
                max-width: 1400px;
                margin: 0 auto;
                background: white;
                padding: 30px;
                border-radius: 15px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            }}
            h1 {{
                color: #2d3748;
                text-align: center;
                margin-bottom: 10px;
            }}
            .subtitle {{
                text-align: center;
                color: #718096;
                margin-bottom: 30px;
            }}
            .stats {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}
            .stat-card {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 10px;
                text-align: center;
            }}
            .stat-value {{
                font-size: 2.5em;
                font-weight: bold;
                margin: 10px 0;
            }}
            .stat-label {{
                font-size: 0.9em;
                opacity: 0.9;
            }}
            .news-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
                gap: 15px;
                margin-top: 20px;
            }}
            .news-card {{
                border: 1px solid #e2e8f0;
                padding: 15px;
                border-radius: 8px;
                transition: transform 0.2s;
            }}
            .news-card:hover {{
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            }}
            .sentiment-positive {{ border-left: 4px solid #48bb78; }}
            .sentiment-negative {{ border-left: 4px solid #f56565; }}
            .sentiment-neutral {{ border-left: 4px solid #cbd5e0; }}
            .news-title {{
                font-weight: 600;
                color: #2d3748;
                margin-bottom: 8px;
                font-size: 0.95em;
            }}
            .news-meta {{
                font-size: 0.85em;
                color: #718096;
            }}
            .sentiment-badge {{
                display: inline-block;
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 0.8em;
                font-weight: 600;
                margin-top: 8px;
            }}
            .badge-positive {{ background: #c6f6d5; color: #22543d; }}
            .badge-negative {{ background: #fed7d7; color: #742a2a; }}
            .badge-neutral {{ background: #e2e8f0; color: #2d3748; }}
            .colcap-info {{
                background: #f7fafc;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
            }}
            .section-title {{
                color: #2d3748;
                border-bottom: 2px solid #667eea;
                padding-bottom: 10px;
                margin: 30px 0 20px 0;
            }}
            .error {{
                background: #fed7d7;
                color: #742a2a;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 News-COLCAP Correlation Analyzer</h1>
            <p class="subtitle">Análisis de Sentimiento de Noticias y Correlación con el Índice COLCAP</p>
            
            {"<div class='error'>⚠️ No hay datos. Ejecuta: 1_run_collector.py</div>" if not news else f'''
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-label">Total Noticias</div>
                    <div class="stat-value">{total}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Sentimiento Promedio</div>
                    <div class="stat-value">{avg_sentiment:+.2f}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Positivas</div>
                    <div class="stat-value">{positive}</div>
                    <div class="stat-label">{positive/total*100:.1f}%</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Negativas</div>
                    <div class="stat-value">{negative}</div>
                    <div class="stat-label">{negative/total*100:.1f}%</div>
                </div>
            </div>
            
            {f"""
            <div class="colcap-info">
                <h3>📈 Datos del COLCAP</h3>
                <p><strong>Último cierre:</strong> {colcap.get('ultimo_cierre', 'N/A'):,.2f}</p>
                <p><strong>Cambio promedio:</strong> {colcap.get('cambio_promedio', 0):+.2f}%</p>
                <p><strong>Volatilidad:</strong> {colcap.get('volatilidad', 0):.2f}%</p>
                <p><strong>Días analizados:</strong> {colcap.get('dias_analizados', 0)}</p>
            </div>
            """ if colcap else ""}
            
            <h2 class="section-title">Últimas Noticias Analizadas</h2>
            <div class="news-grid">
                {"".join([f'''
                <div class="news-card sentiment-{n['sentiment_label']}">
                    <div class="news-title">{n['title']}</div>
                    <div class="news-meta">Fuente: {n['domain']}</div>
                    <div class="news-meta">Categorías: {", ".join(n['categories'])}</div>
                    <span class="sentiment-badge badge-{n['sentiment_label']}">
                        {n['sentiment_label'].upper()} ({n['sentiment_score']:+.2f})
                    </span>
                </div>
                ''' for n in news[:12]])}
            </div>
            '''}
            
            <div style="text-align: center; margin-top: 40px; color: #718096;">
                <p>🚀 Sistema de Análisis de Noticias Económicas de Colombia</p>
                <p>Infraestructuras Paralelas y Distribuidas - 2025</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("Iniciando Dashboard Web")
    print("=" * 60)
    print("\nAccede a: http://localhost:8000")
    print("\nPresiona Ctrl+C para detener\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="error")
