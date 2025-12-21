"""
Generador de conclusiones y análisis de sentimiento vs COLCAP
"""
import psycopg2
from datetime import datetime, timedelta
import statistics

DB_CONFIG = {
    'host': 'localhost',
    'database': 'news_colcap',
    'user': 'newsuser',
    'password': 'newspass123',
    'port': 5432
}

def generar_conclusiones():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Obtener estadísticas de noticias
    cur.execute("""
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
    
    news_stats = cur.fetchone()
    total, positivas, negativas, neutrales, avg_sent, std_sent = news_stats
    
    # Obtener estadísticas COLCAP (últimos 30 días)
    cur.execute("""
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
    
    colcap_stats = cur.fetchone()
    avg_change, volatilidad, max_change, min_change, max_price, min_price, dias_datos = colcap_stats
    
    cur.close()
    conn.close()
    
    # Generar conclusiones
    conclusiones = {
        "resumen_general": generar_resumen_general(total, positivas, negativas, neutrales),
        "analisis_sentimiento": analizar_sentimiento(positivas, negativas, neutrales, total, avg_sent, std_sent),
        "analisis_colcap": analizar_colcap(avg_change, volatilidad, max_change, min_change, dias_datos),
        "interpretacion": generar_interpretacion(avg_sent, avg_change, positivas, negativas, total),
        "recomendaciones": generar_recomendaciones(avg_sent, avg_change, volatilidad),
        "metricas": {
            "noticias": {
                "total": total,
                "positivas": positivas,
                "negativas": negativas,
                "neutrales": neutrales,
                "sentimiento_promedio": float(avg_sent) if avg_sent else 0.0,
                "volatilidad_sentimiento": float(std_sent) if std_sent else 0.0
            },
            "colcap": {
                "dias_analizados": dias_datos,
                "cambio_promedio": float(avg_change) if avg_change else 0.0,
                "volatilidad": float(volatilidad) if volatilidad else 0.0,
                "mejor_dia": float(max_change) if max_change else 0.0,
                "peor_dia": float(min_change) if min_change else 0.0,
                "precio_maximo": float(max_price) if max_price else 0.0,
                "precio_minimo": float(min_price) if min_price else 0.0
            }
        }
    }
    
    return conclusiones

def generar_resumen_general(total, positivas, negativas, neutrales):
    pct_pos = (positivas / total * 100) if total > 0 else 0
    pct_neg = (negativas / total * 100) if total > 0 else 0
    pct_neu = (neutrales / total * 100) if total > 0 else 0
    
    return f"""Se analizaron {total} noticias relacionadas con la economía colombiana y el mercado financiero. 
La distribución del sentimiento es: {pct_pos:.1f}% positivas ({positivas} noticias), 
{pct_neg:.1f}% negativas ({negativas} noticias) y {pct_neu:.1f}% neutrales ({neutrales} noticias)."""

def analizar_sentimiento(positivas, negativas, neutrales, total, avg_sent, std_sent):
    if total == 0:
        return "No hay datos suficientes para analizar."
    
    pct_neg = (negativas / total * 100)
    pct_pos = (positivas / total * 100)
    
    if avg_sent < -0.1:
        tono = "NEGATIVO"
        descripcion = "Las noticias analizadas reflejan preocupación en el mercado"
    elif avg_sent > 0.1:
        tono = "POSITIVO"
        descripcion = "Las noticias analizadas reflejan optimismo en el mercado"
    else:
        tono = "NEUTRAL"
        descripcion = "Las noticias analizadas reflejan estabilidad en el mercado"
    
    volatilidad_desc = "alta" if std_sent and std_sent > 0.3 else "moderada" if std_sent and std_sent > 0.15 else "baja"
    std_sent_val = float(std_sent) if std_sent else 0.0
    avg_sent_val = float(avg_sent) if avg_sent else 0.0
    
    return f"""El sentimiento general de las noticias es {tono} (score: {avg_sent_val:.3f}). 
{descripcion}, con una volatilidad {volatilidad_desc} (σ={std_sent_val:.3f}).

El análisis revela que hay {pct_neg:.1f}% de noticias negativas, lo cual {"sugiere preocupaciones importantes" if pct_neg > 25 else "está dentro de rangos normales"}."""

def analizar_colcap(avg_change, volatilidad, max_change, min_change, dias_datos):
    if not avg_change:
        return "No hay datos suficientes del COLCAP para analizar."
    
    if avg_change > 0.5:
        tendencia = "ALCISTA"
        descripcion = "El índice muestra una tendencia claramente positiva"
    elif avg_change < -0.5:
        tendencia = "BAJISTA"
        descripcion = "El índice muestra una tendencia negativa"
    else:
        tendencia = "LATERAL"
        descripcion = "El índice se mantiene relativamente estable"
    
    volatilidad_desc = "ALTA" if volatilidad and volatilidad > 2.0 else "MODERADA" if volatilidad and volatilidad > 1.0 else "BAJA"
    
    vol_val = float(volatilidad) if volatilidad else 0.0
    avg_val = float(avg_change) if avg_change else 0.0
    max_val = float(max_change) if max_change else 0.0
    min_val = float(min_change) if min_change else 0.0
    
    return f"""Durante los últimos {dias_datos} días analizados, el COLCAP muestra una tendencia {tendencia}.
{descripcion}, con un cambio promedio diario de {avg_val:+.2f}%.

La volatilidad del índice es {volatilidad_desc} ({vol_val:.2f}%), 
con un mejor día de {max_val:+.2f}% y un peor día de {min_val:+.2f}%."""

def generar_interpretacion(avg_sent, avg_change, positivas, negativas, total):
    pct_neg = (negativas / total * 100) if total > 0 else 0
    pct_pos = (positivas / total * 100) if total > 0 else 0
    
    interpretacion = []
    
    # Análisis de coherencia
    if avg_sent < -0.05 and avg_change and avg_change < 0:
        interpretacion.append("✓ COHERENCIA: El sentimiento negativo en noticias coincide con la caída del índice COLCAP.")
    elif avg_sent > 0.05 and avg_change and avg_change > 0:
        interpretacion.append("✓ COHERENCIA: El sentimiento positivo en noticias coincide con el alza del índice COLCAP.")
    elif avg_sent < -0.05 and avg_change and avg_change > 0:
        interpretacion.append("⚠ DIVERGENCIA: A pesar del sentimiento negativo en noticias, el COLCAP muestra tendencia alcista.")
    elif avg_sent > 0.05 and avg_change and avg_change < 0:
        interpretacion.append("⚠ DIVERGENCIA: A pesar del sentimiento positivo en noticias, el COLCAP muestra tendencia bajista.")
    
    # Análisis de distribución
    if pct_neg > 30:
        interpretacion.append(f"⚠ ALERTA: Alto porcentaje de noticias negativas ({pct_neg:.1f}%) sugiere preocupaciones en el mercado.")
    elif pct_pos > 20:
        interpretacion.append(f"✓ OPTIMISMO: Buen porcentaje de noticias positivas ({pct_pos:.1f}%) sugiere confianza en el mercado.")
    
    return "\n".join(interpretacion) if interpretacion else "Los datos sugieren un mercado en equilibrio sin señales fuertes."

def generar_recomendaciones(avg_sent, avg_change, volatilidad):
    recomendaciones = []
    
    if volatilidad and volatilidad > 2.0:
        recomendaciones.append("• Alta volatilidad detectada: Se recomienda precaución en operaciones de corto plazo.")
    
    if avg_sent < -0.15:
        recomendaciones.append("• Sentimiento mayormente negativo: Considerar estrategias defensivas o esperar señales de recuperación.")
    elif avg_sent > 0.15:
        recomendaciones.append("• Sentimiento positivo: El mercado muestra confianza, favorable para posiciones largas.")
    
    if avg_change and avg_change > 0.5:
        recomendaciones.append("• Tendencia alcista fuerte: Momento favorable para inversiones con horizonte de mediano plazo.")
    elif avg_change and avg_change < -0.5:
        recomendaciones.append("• Tendencia bajista: Evaluar oportunidades de compra en niveles de soporte clave.")
    
    if not recomendaciones:
        recomendaciones.append("• Mercado estable: Mantener estrategia actual y monitorear cambios en sentimiento.")
    
    return recomendaciones

if __name__ == "__main__":
    import json
    
    print("=" * 70)
    print("GENERANDO CONCLUSIONES DEL ANÁLISIS SENTIMIENTO VS COLCAP")
    print("=" * 70)
    print()
    
    conclusiones = generar_conclusiones()
    
    print("📊 RESUMEN GENERAL")
    print("-" * 70)
    print(conclusiones["resumen_general"])
    print()
    
    print("💭 ANÁLISIS DE SENTIMIENTO")
    print("-" * 70)
    print(conclusiones["analisis_sentimiento"])
    print()
    
    print("📈 ANÁLISIS DEL COLCAP")
    print("-" * 70)
    print(conclusiones["analisis_colcap"])
    print()
    
    print("🔍 INTERPRETACIÓN")
    print("-" * 70)
    print(conclusiones["interpretacion"])
    print()
    
    print("💡 RECOMENDACIONES")
    print("-" * 70)
    for rec in conclusiones["recomendaciones"]:
        print(rec)
    print()
    
    # Guardar en JSON
    with open('data/conclusiones.json', 'w', encoding='utf-8') as f:
        json.dump(conclusiones, f, indent=2, ensure_ascii=False)
    
    print("=" * 70)
    print("✅ Conclusiones guardadas en: data/conclusiones.json")
    print("=" * 70)
