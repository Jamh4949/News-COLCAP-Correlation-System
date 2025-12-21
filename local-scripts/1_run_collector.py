"""
DEMO SIMPLIFICADA - Collector
Obtiene noticias reales de GDELT y las guarda en JSON
"""
import json
import requests
from datetime import datetime, timedelta
import time

print("=" * 60)
print("DEMO: GDELT News Collector")
print("=" * 60)

# Keywords económicos
economic_keywords = [
    'economia', 'business', 'finance', 'market', 'bank', 'trade'
]

# Calcular rango de fechas (últimas 24 horas)
end_date = datetime.utcnow()
start_date = end_date - timedelta(hours=24)
start_str = start_date.strftime('%Y%m%d%H%M%S')
end_str = end_date.strftime('%Y%m%d%H%M%S')

print(f"\nBuscando noticias de Colombia desde {start_date.strftime('%Y-%m-%d %H:%M')}")
print(f"Keywords: {', '.join(economic_keywords)}")

articles = []

# Buscar por cada keyword
for i, keyword in enumerate(economic_keywords, 1):  # Todos los keywords
    print(f"\n[{i}/{len(economic_keywords)}] Buscando '{keyword}'...", end=" ")
    
    try:
        url = "https://api.gdeltproject.org/api/v2/doc/doc"
        params = {
            'query': f'colombia {keyword}',
            'mode': 'artlist',
            'maxrecords': 20,
            'startdatetime': start_str,
            'enddatetime': end_str,
            'format': 'json'
        }
        
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if 'articles' in data:
                count = len(data['articles'])
                articles.extend(data['articles'])
                print(f"OK ({count} articulos)")
            else:
                print("Sin resultados")
        else:
            print(f"Error {response.status_code}")
        
        time.sleep(1)  # Rate limiting
        
    except Exception as e:
        print(f"Error: {str(e)}")

# Eliminar duplicados
unique_articles = {article['url']: article for article in articles}
articles_list = list(unique_articles.values())

print(f"\n{'='*60}")
print(f"RESULTADOS:")
print(f"  Total articulos encontrados: {len(articles)}")
print(f"  Articulos unicos: {len(articles_list)}")
print(f"{'='*60}")

# Guardar en JSON
output_file = 'data/news.json'
import os
os.makedirs('data', exist_ok=True)

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(articles_list, f, indent=2, ensure_ascii=False)

print(f"\nGuardado en: {output_file}")

# Mostrar primeros 5 artículos
print(f"\nPRIMEROS 5 ARTICULOS:")
print("-" * 60)
for i, article in enumerate(articles_list[:5], 1):
    title = article.get('title', 'Sin titulo')
    domain = article.get('domain', 'Desconocido')
    print(f"\n{i}. {title}")
    print(f"   Fuente: {domain}")
    print(f"   URL: {article.get('url', '')[:60]}...")

print(f"\n{'='*60}")
print(f"DEMO COMPLETADA!")
print(f"Siguiente paso: Ejecutar 2_run_processor.py")
print(f"{'='*60}")
