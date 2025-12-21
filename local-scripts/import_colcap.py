"""
Script para importar datos COLCAP a Docker PostgreSQL
"""
import json
import psycopg2
from datetime import datetime
from psycopg2.extras import execute_values

DB_CONFIG = {
    'host': 'localhost',
    'database': 'news_colcap',
    'user': 'newsuser',
    'password': 'newspass123',
    'port': 5432
}

print("📈 Importando datos COLCAP a Docker PostgreSQL...")

with open('data/colcap_data_full.json', 'r', encoding='utf-8') as f:
    datos = json.load(f)

print(f"   Encontrados {len(datos)} registros")

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

values = []
for record in datos:
    fecha_str = record['fecha']
    date_obj = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    
    values.append((
        date_obj,
        record['apertura'],
        record['maximo'],
        record['minimo'],
        record['cierre'],
        int(record['volumen']),
        record['cierre'],  # adj_close = close
        record['cambio_diario']
    ))

insert_query = """
    INSERT INTO colcap_data (date, open_price, high_price, low_price, 
                            close_price, volume, adj_close, daily_change)
    VALUES %s
    ON CONFLICT (date) DO UPDATE SET
        open_price = EXCLUDED.open_price,
        high_price = EXCLUDED.high_price,
        low_price = EXCLUDED.low_price,
        close_price = EXCLUDED.close_price,
        volume = EXCLUDED.volume,
        adj_close = EXCLUDED.adj_close,
        daily_change = EXCLUDED.daily_change
"""

execute_values(cur, insert_query, values)
inserted = cur.rowcount

conn.commit()
cur.close()
conn.close()

print(f"   ✅ Importados/actualizados {inserted} registros COLCAP")

# Verificar
conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM colcap_data")
total = cur.fetchone()[0]
cur.execute("SELECT MIN(date), MAX(date) FROM colcap_data")
min_date, max_date = cur.fetchone()
cur.close()
conn.close()

print(f"\n📊 Verificación:")
print(f"   Total registros COLCAP: {total}")
print(f"   Rango de fechas: {min_date} a {max_date}")
print(f"\n✅ ¡Datos COLCAP importados exitosamente!")
