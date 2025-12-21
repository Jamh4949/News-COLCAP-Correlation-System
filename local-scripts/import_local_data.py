"""
Script para importar datos locales (JSON) a la base de datos Docker
"""
import json
import psycopg2
from datetime import datetime
from psycopg2.extras import execute_values

# Configuración de la base de datos Docker
DB_CONFIG = {
    'host': 'localhost',
    'database': 'news_colcap',
    'user': 'newsuser',
    'password': 'newspass123',
    'port': 5432
}

def import_news():
    """Importar noticias desde data/news.json"""
    print("📰 Importando noticias desde data/news.json...")
    
    with open('data/news.json', 'r', encoding='utf-8') as f:
        news_data = json.load(f)
    
    print(f"   Encontradas {len(news_data)} noticias en archivo local")
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Leer noticias procesadas para obtener sentimientos
    try:
        with open('data/processed_news.json', 'r', encoding='utf-8') as f:
            processed_data = json.load(f)
            sentiment_map = {item['url']: item for item in processed_data}
    except:
        sentiment_map = {}
    
    # Preparar datos para inserción
    values = []
    for article in news_data:
        url = article.get('url', '')
        title = article.get('title', '')
        content = article.get('description', '')
        source = article.get('source', '')
        
        # Parsear fecha
        date_str = article.get('date', '')
        try:
            published_date = datetime.strptime(date_str, '%Y%m%dT%H%M%SZ')
        except:
            published_date = datetime.utcnow()
        
        # Obtener sentimiento si existe
        sentiment_score = None
        sentiment_label = None
        if url in sentiment_map:
            sentiment_score = sentiment_map[url].get('sentiment_score', 0.0)
            sentiment_label = sentiment_map[url].get('sentiment_label', 'neutral')
        
        values.append((
            url, title, content, source, published_date,
            'CO', sentiment_score, sentiment_label, None, None
        ))
    
    # Insertar en batch con ON CONFLICT para evitar duplicados
    insert_query = """
        INSERT INTO news (url, title, content, source, published_date, country, 
                         sentiment_score, sentiment_label, categories, keywords)
        VALUES %s
        ON CONFLICT (url) DO NOTHING
    """
    
    execute_values(cur, insert_query, values)
    inserted = cur.rowcount
    
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"   ✅ Importadas {inserted} noticias nuevas a Docker PostgreSQL")
    return inserted

def import_colcap():
    """Importar datos COLCAP desde data/colcap_data.json"""
    print("\n📈 Importando datos COLCAP desde data/colcap_data.json...")
    
    try:
        with open('data/colcap_data.json', 'r', encoding='utf-8') as f:
            colcap_json = json.load(f)
    except:
        print("   ⚠️  No se encontró colcap_data.json")
        return 0
    
    # El archivo tiene un campo 'datos' con la lista de registros
    colcap_data = colcap_json.get('datos', [])
    
    if not colcap_data:
        print("   ⚠️  Archivo COLCAP vacío o sin campo 'datos'")
        return 0
    
    print(f"   Encontrados {len(colcap_data)} registros de COLCAP")
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    values = []
    for record in colcap_data:
        fecha_str = record.get('fecha', '')
        try:
            date_obj = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except:
            try:
                # Intentar formato alternativo
                date_obj = datetime.fromisoformat(fecha_str).date()
            except:
                continue
        
        values.append((
            date_obj,
            record.get('apertura'),
            record.get('maximo'),
            record.get('minimo'),
            record.get('cierre'),
            record.get('volumen', 0),
            record.get('cierre'),  # adj_close = close
            record.get('cambio_diario', 0.0)
        ))
    
    if not values:
        print("   ⚠️  No se pudieron parsear registros COLCAP")
        return 0
    
    insert_query = """
        INSERT INTO colcap_data (date, open_price, high_price, low_price, 
                                close_price, volume, adj_close, daily_change)
        VALUES %s
        ON CONFLICT (date) DO UPDATE SET
            close_price = EXCLUDED.close_price,
            volume = EXCLUDED.volume,
            daily_change = EXCLUDED.daily_change
    """
    
    from psycopg2.extras import execute_values
    execute_values(cur, insert_query, values)
    inserted = cur.rowcount
    
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"   ✅ Importados {inserted} registros COLCAP a Docker PostgreSQL")
    return inserted

def verify_import():
    """Verificar los datos importados"""
    print("\n🔍 Verificando datos importados...")
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Contar noticias
    cur.execute("SELECT COUNT(*) FROM news")
    total_news = cur.fetchone()[0]
    
    # Contar por sentimiento
    cur.execute("""
        SELECT sentiment_label, COUNT(*) 
        FROM news 
        WHERE sentiment_score IS NOT NULL 
        GROUP BY sentiment_label
    """)
    sentiment_counts = cur.fetchall()
    
    # Contar COLCAP
    cur.execute("SELECT COUNT(*) FROM colcap_data")
    total_colcap = cur.fetchone()[0]
    
    cur.close()
    conn.close()
    
    print(f"\n📊 RESUMEN:")
    print(f"   Total noticias: {total_news}")
    if sentiment_counts:
        for label, count in sentiment_counts:
            print(f"   - {label}: {count}")
    print(f"   Total datos COLCAP: {total_colcap}")

if __name__ == "__main__":
    print("=" * 60)
    print("  IMPORTACIÓN DE DATOS LOCALES A DOCKER")
    print("=" * 60)
    
    try:
        news_count = import_news()
        colcap_count = import_colcap()
        verify_import()
        
        print("\n✅ Importación completada exitosamente!")
        print("\n💡 Ahora reinicia el processor para que procese las noticias:")
        print("   docker restart proyectofinal-processor-1")
        
    except Exception as e:
        print(f"\n❌ Error durante la importación: {e}")
        import traceback
        traceback.print_exc()
