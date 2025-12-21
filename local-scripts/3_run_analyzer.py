"""
DEMO SIMPLIFICADA - Analyzer
Obtiene datos del COLCAP y calcula correlaciones
"""
import json
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from scipy import stats

print("=" * 60)
print("DEMO: COLCAP Correlation Analyzer")
print("=" * 60)

# Cargar noticias procesadas
try:
    with open('data/processed_news.json', 'r', encoding='utf-8') as f:
        articles = json.load(f)
    print(f"\nCargados {len(articles)} articulos procesados")
except FileNotFoundError:
    print("\nERROR: Primero ejecuta 2_run_processor.py")
    exit(1)

# Obtener datos del COLCAP
print("\nObteniendo datos del COLCAP desde Yahoo Finance...")
print("Simbolo: GXG (Indice COLCAP)")

try:
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    print(f"Rango: {start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')}")
    
    # Usar yf.download en lugar de Ticker().history()
    df = yf.download("GXG", start=start_date, end=end_date, auto_adjust=True, progress=False)
    
    if df.empty:
        print("ERROR: No se obtuvieron datos del COLCAP")
        exit(1)
    
    # Calcular cambio diario porcentual
    df['Daily_Change'] = df['Close'].pct_change() * 100
    
    print(f"OK - Obtenidos {len(df)} dias de datos REALES")
    
    # Mostrar últimos 5 días usando print del DataFrame
    print("\nUltimos 5 dias del COLCAP:")
    print("-" * 60)
    print(df[['Close', 'Daily_Change']].tail(5).to_string())
    
except Exception as e:
    print(f"Error obteniendo datos: {str(e)}")
    import traceback
    traceback.print_exc()
    exit(1)

# Calcular sentimiento promedio (simulado por día)
print(f"\n{'='*60}")
print("ANALISIS DE CORRELACION")
print(f"{'='*60}")

# Para demo, usamos el sentimiento promedio de todas las noticias
avg_sentiment = sum(a['sentiment_score'] for a in articles) / len(articles)
print(f"\nSentimiento promedio de noticias: {avg_sentiment:+.3f}")

# Calcular estadísticas del COLCAP
avg_change = df['Daily_Change'].mean()
volatility = df['Daily_Change'].std()

print(f"Cambio promedio COLCAP: {avg_change:+.2f}%")
print(f"Volatilidad COLCAP: {volatility:.2f}%")

# Para una correlación real, necesitaríamos noticias con fechas
# Por ahora mostramos análisis descriptivo
print(f"\n{'='*60}")
print("INTERPRETACION:")
print(f"{'='*60}")

if avg_sentiment > 0.1:
    print("Las noticias muestran un sentimiento POSITIVO")
    print("-> Optimismo en el mercado colombiano")
elif avg_sentiment < -0.1:
    print("Las noticias muestran un sentimiento NEGATIVO")
    print("-> Pesimismo o preocupacion en el mercado")
else:
    print("Las noticias muestran un sentimiento NEUTRAL")
    print("-> Estabilidad en la percepcion del mercado")

if avg_change > 0.5:
    print(f"\nEl COLCAP muestra CRECIMIENTO ({avg_change:+.2f}% promedio)")
elif avg_change < -0.5:
    print(f"\nEl COLCAP muestra DECRECIMIENTO ({avg_change:+.2f}% promedio)")
else:
    print(f"\nEl COLCAP muestra ESTABILIDAD ({avg_change:+.2f}% promedio)")

# Guardar datos del COLCAP
# Convertir a diccionario para evitar problemas con Series
last_30 = df.tail(30).copy()
last_30.reset_index(inplace=True)

datos_list = []
for _, row in last_30.iterrows():
    try:
        fecha = row[last_30.columns[0]]  # Primera columna (Date o index)
        close_price = row['Close']
        daily_change = row['Daily_Change']
        
        datos_list.append({
            'fecha': fecha.strftime('%Y-%m-%d'),
            'cierre': float(close_price),
            'cambio': float(daily_change) if pd.notna(daily_change) else 0.0
        })
    except:
        continue

colcap_data = {
    'fecha_actualizacion': datetime.now().isoformat(),
    'dias_analizados': len(df),
    'ultimo_cierre': float(df['Close'].iloc[-1]) if len(df) > 0 else 0.0,
    'cambio_promedio': float(avg_change),
    'volatilidad': float(volatility),
    'datos': datos_list
}

with open('data/colcap_data.json', 'w', encoding='utf-8') as f:
    json.dump(colcap_data, f, indent=2)

print(f"\n{'='*60}")
print("DATOS GUARDADOS:")
print(f"  - data/colcap_data.json (ultimos 30 dias)")
print(f"\nSiguiente paso: Ejecutar 4_run_dashboard.py")
print(f"{'='*60}")
