"""
Test rápido del ticker GXG
"""
import yfinance as yf
from datetime import datetime, timedelta

print("Probando ticker GXG...")

end_date = datetime.now()
start_date = end_date - timedelta(days=90)

df = yf.download("GXG", start=start_date, end=end_date, auto_adjust=True, progress=False)

print(f"\nObtenidos {len(df)} dias de datos")
print(f"\nUltimos 5 dias:")
print(df[['Close']].tail(5))

df['Daily_Change'] = df['Close'].pct_change() * 100
print(f"\nCon cambios diarios:")
print(df[['Close', 'Daily_Change']].tail(5))

print(f"\nEstadisticas:")
print(f"Cambio promedio: {df['Daily_Change'].mean():.2f}%")
print(f"Volatilidad: {df['Daily_Change'].std():.2f}%")
print(f"Ultimo cierre: {df['Close'].iloc[-1]:.2f}")
