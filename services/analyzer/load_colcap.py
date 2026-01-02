import psycopg2
import pandas as pd

print("Cargando COLCAP desde JSON...")

df = pd.read_json("/data/colcap_data_full.json")

# Normalización EXACTA según el JSON real
df['date'] = pd.to_datetime(df['fecha']).dt.date
df['close'] = df['cierre']

df = df[['date', 'close']]

print("Filas a cargar:", len(df))

print("Conectando a Postgres...")
conn = psycopg2.connect(
    host="postgres",
    database="news_colcap",
    user="newsuser",
    password="newspass123"
)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS colcap_prices (
    date DATE PRIMARY KEY,
    close NUMERIC
)
""")

cur.execute("TRUNCATE colcap_prices")

for _, r in df.iterrows():
    cur.execute(
        "INSERT INTO colcap_prices(date, close) VALUES (%s, %s)",
        (r.date, float(r.close))
    )

conn.commit()
cur.close()
conn.close()

print("COLCAP HISTÓRICO CARGADO:", len(df))
