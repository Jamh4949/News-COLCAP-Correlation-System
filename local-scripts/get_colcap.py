import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import json

print("Obteniendo datos COLCAP de todo 2025 desde Yahoo Finance...")
end = datetime.now()
start = datetime(2025, 1, 1)  # Desde el 1 de enero de 2025

df = yf.download('GXG', start=start, end=end, auto_adjust=True, progress=False)

# Aplanar columnas si son multiíndice
if isinstance(df.columns, pd.MultiIndex):
    df.columns = [col[0] if col[1] == '' else col[0] for col in df.columns]

df['Daily_Change'] = df['Close'].pct_change() * 100
df.reset_index(inplace=True)

print(f"Obtenidos {len(df)} días de datos")
print(f"Columnas: {df.columns.tolist()}")

datos = []
for idx in range(len(df)):
    fecha_val = df.iloc[idx]['Date']
    if hasattr(fecha_val, 'strftime'):
        fecha_str = fecha_val.strftime('%Y-%m-%d')
    else:
        fecha_str = str(fecha_val)[:10]
    
    datos.append({
        'fecha': fecha_str,
        'apertura': df.iloc[idx]['Open'],
        'maximo': df.iloc[idx]['High'],
        'minimo': df.iloc[idx]['Low'],
        'cierre': df.iloc[idx]['Close'],
        'volumen': int(df.iloc[idx]['Volume']),
        'cambio_diario': df.iloc[idx]['Daily_Change'] if pd.notna(df.iloc[idx]['Daily_Change']) else 0.0
    })

with open('data/colcap_data_full.json', 'w', encoding='utf-8') as f:
    json.dump(datos, f, indent=2, ensure_ascii=False)

print(f"✅ Guardados {len(datos)} registros en data/colcap_data_full.json")
